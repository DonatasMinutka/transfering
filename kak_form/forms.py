from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from dcim.forms import SiteForm
from tenancy.forms import TenantForm
from tenancy.models import Tenant
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from dcim.models import Device, DeviceType, DeviceRole, Interface, Site
from extras.models import ConfigTemplate
from utilities.forms.fields import DynamicModelChoiceField
from ipam.models import IPAddress, VRF
import ipaddress
from tenancy.models import TenantGroup
import logging
from django.utils.translation import gettext_lazy as _



import sys
logger = logging.getLogger(__name__)

def validate_ipv4(value):
    if value:
        try:
            ipaddress.IPv4Address(value)
        except ValueError:
            raise ValidationError('Enter a valid IPv4 address(e.g., 192.168.1.1)')
    
def validate_ipv4_cidr(value):
    if value:
        if '/' not in value:
            raise ValidationError('Enter valid IP with CIDR notation(e.g., 192.168.1.0/32)')
        try:
            ipaddress.IPv4Network(value, strict=False)
        except ValueError:
            raise ValidationError('Enter valid IP with CIDR notation(e.g., 192.168.1.0/32)')

class CustomDeviceForm(forms.ModelForm):
    SERVICE_CHOICES = [
        ('', '--- Select Service ---'), 
        ('capn', 'CAPN'),
        ('internet', 'Internet'),
        ('isop', 'ISOP'),
        ('nkdps', 'NKDPS'),
        ('wan_failover', 'WAN FAILOVER'),
        ('lte_5g_nokia', 'LTE 5G From Nokia'),
    ]

    Services = forms.ChoiceField(choices=SERVICE_CHOICES, required=True, label="Services / Paslaugos", widget=forms.Select(attrs={'class': 'form-control'}))
    Given_WAN_Address = forms.CharField(max_length=50, required=True, validators=[validate_ipv4], widget=forms.TextInput(attrs={'placeholder': '192.168.1.1','class': 'form-control'}), label="WAN IP Address")
    LAN_IP_Address_And_Subnet_Mask = forms.CharField(max_length=50, required=True, validators=[validate_ipv4_cidr], widget=forms.TextInput(attrs={'placeholder': '192.168.1.1/32','class': 'form-control'}), label="LAN IP Address Ir Subnet")
    Service_ID = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': '********','class': 'form-control'}), label="PID")
    Enable_DHCP = forms.BooleanField(required=False, label="Enable DHCP", widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'enable_dhcp_checkbox'}))
    DHCP_Start_Address = forms.CharField(max_length=50, required=False, validators=[validate_ipv4], widget=forms.TextInput(attrs={'class': 'form-control dhcp-field'}), label="DHCP Start Address")
    DHCP_End_Address = forms.CharField(max_length=50, required=False, validators=[validate_ipv4], widget=forms.TextInput(attrs={'class': 'form-control dhcp-field'}), label="DHCP End Address")
    CAPN_Address = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': '192.168.1.1','class': 'form-control'}), label="CAPN Address")
    
    class Meta:
        model = Device
        fields = ['name', 'role', 'device_type','tenant', 'site']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['device_type'] = DynamicModelChoiceField(
            queryset=DeviceType.objects.all(),
            query_params={
                'tag': '$Services' 
            },
            required=True
            )
        self.fields['name'].widget.attrs.update({
        'id': 'id_name',
        'class': 'form-control',
        })
        self.fields['tenant'].label = 'Tenant / Įmonė'
        self.fields['site'].label = 'Site / Vieta'
        self.fields['name'].label = 'Name / Pavadinimas'  
        self.fields['device_type'].label = 'Device Type / Modelis'  
        
        try:
            cpe_role = DeviceRole.objects.get(name='CPE')
            self.fields['role'].queryset = DeviceRole.objects.filter(name='CPE')
            self.fields['role'].initial = cpe_role
            self.fields['role'].empty_label = None  
            self.fields['role'].widget.attrs.update({
                'class': 'hide-role-field',
            })    
        except DeviceRole.DoesNotExist:
            return
        self._original_service = None
        self._original_device_type = None
        if self.instance and self.instance.pk:
            if self.instance.local_context_data and 'KAK_DATA' in self.instance.local_context_data:
                kak_data = self.instance.local_context_data['KAK_DATA']
                self._original_service = kak_data.get('services', '')

            if self.instance.device_type:
                self._original_device_type = self.instance.device_type
    
    
        self.fields['name'].help_text = mark_safe(
        '<script src="/static/kak_form/js/auto_name.js"></script>'
        )   
        self.fields['role'].help_text = mark_safe(
            '<link rel="stylesheet" href="/static/kak_form/css/custom.css">'
        )
        self.fields['device_type'].widget.attrs['id'] = 'id_device_type'
        self.fields['device_type'].widget.attrs['data-custom-display'] = 'manufacturer-model'
        
        field_order = ['name', 'role', 'Services', 'device_type', 'site']
        self.order_fields(field_order)


        self.fields['device_type'].help_text = mark_safe(
            '<script src="/static/kak_form/js/device_type_display.js"></script>'
        )

        self.fields['site'].help_text = mark_safe(
            '<script src="/static/kak_form/js/site_refresh.js"></script>'
        )
        self.fields['tenant'].help_text = mark_safe(
            '<script src="/static/kak_form/js/tenant_refresh.js"></script>'
        )
        self.fields['DHCP_End_Address'].help_text = mark_safe(
            '<script src="/static/kak_form/js/dhcp_toggle.js"></script>'
        )
        self.fields['Services'].help_text = mark_safe(
            '<script src="/static/kak_form/js/extra_fields.js"></script>'
        )
        if self.instance and self.instance.pk:
            if self.instance.local_context_data and 'KAK_DATA' in self.instance.local_context_data:
                kak_data = self.instance.local_context_data['KAK_DATA']
                self.fields['CAPN_Address'].initial = kak_data.get('capn', '')
                self.fields['Enable_DHCP'].initial = kak_data.get('enable_dhcp', False)
                self.fields['Services'].initial = kak_data.get('services', '')
                self.fields['Given_WAN_Address'].initial = kak_data.get('wan', '')
                self.fields['LAN_IP_Address_And_Subnet_Mask'].initial = kak_data.get('lan', '')
                self.fields['Service_ID'].initial = kak_data.get('service_id', '')
                self.fields['DHCP_Start_Address'].initial = kak_data.get('dhcp_start', '')
                self.fields['DHCP_End_Address'].initial = kak_data.get('dhcp_end', '')

    def _get_auto_config_template(self):
        device = self.instance
        device_type = None
        service = None
        service = self.data.get('Services')
        if device.pk:
            device_type = device.device_type
        else:
            device_type_id = self.data.get('device_type')
            try:
                if device_type_id:
                    device_type = DeviceType.objects.get(pk=device_type_id)
            except (DeviceType.DoesNotExist, DeviceRole.DoesNotExist, ValueError):
                return None
            
        if not device_type or not service or not device_type.manufacturer:
            return None
        search_name = f"{device_type.manufacturer}_{device_type.model}_{service}".replace(' ', '_')
        template = ConfigTemplate.objects.filter(
            name__icontains=search_name
        ).first()
        return template


    def _check_duplicate_ip(self, ip_address, vrf):
        interface_ct = ContentType.objects.get_for_model(Interface)
        existing_ip = IPAddress.objects.filter(address=ip_address)
        existing_ip = existing_ip.filter(vrf=vrf) if vrf else existing_ip.filter(vrf__isnull=True)

        if self.instance.pk:
            own_interface_ids = list(
                Interface.objects.filter(device_id=self.instance.pk).values_list("id", flat=True)
            )
            if own_interface_ids:
                existing_ip = existing_ip.exclude(
                    assigned_object_type=interface_ct,
                    assigned_object_id__in=own_interface_ids,
                )

        if existing_ip.exists():
            vrf_name = vrf.name if vrf else "No VRF"
            raise forms.ValidationError(
                f"Duplicate IP found in VRF {vrf_name}: {existing_ip.first()}"
            )

    def _check_dhcp_range(self,lan_ip,dhcp_start,dhcp_end):
        if not all([lan_ip, dhcp_start, dhcp_end]):
            return None
        net = ipaddress.ip_network(lan_ip, strict=False)
        start = ipaddress.ip_address(dhcp_start)
        end = ipaddress.ip_address(dhcp_end)
        first_host = net.network_address + 1
        last_host = net.broadcast_address - 1
        return first_host <= start <= last_host and first_host <= end <= last_host

    def clean(self):
        cleaned_data = super().clean()
        lan_ip = cleaned_data.get('LAN_IP_Address_And_Subnet_Mask')
        lan_ip_no_mask = lan_ip.split('/')[0] if lan_ip and '/' in lan_ip else lan_ip
        wan_ip = cleaned_data.get('Given_WAN_Address')
        service_id = cleaned_data.get('Service_ID')
        tenant = cleaned_data.get('tenant')
        name = cleaned_data.get('name')
        site = cleaned_data.get('site')
        device_type = cleaned_data.get('device_type')
        role = cleaned_data.get('role')
        dhcp_start = cleaned_data.get('DHCP_Start_Address')
        dhcp_end = cleaned_data.get('DHCP_End_Address')
        enable_dhcp = cleaned_data.get('Enable_DHCP')
        config_template = cleaned_data.get('config_template')



        if name:
            existing_device = Device.objects.filter(name=name)
            if self.instance.pk:
                existing_device = existing_device.exclude(pk=self.instance.pk)
            
            if existing_device.exists():
                
                raise forms.ValidationError(f'A device with name "{name}" already exists.')

        if enable_dhcp:
            if dhcp_start and dhcp_end:
                if not self._check_dhcp_range(lan_ip, dhcp_start, dhcp_end):
                    raise forms.ValidationError("DHCP range is not correct.")

        if lan_ip_no_mask and wan_ip:
            if lan_ip_no_mask == wan_ip:
                raise forms.ValidationError("WAN and LAN IP addresses cannot be the same.")

        if service_id:
                if not service_id.isdigit():
                    raise forms.ValidationError("Service ID may only contain digits.")
                if len(service_id) != 8:
                    raise forms.ValidationError("Service ID must be exactly 8 digits.")

        vrf = None
        if tenant:
            try:
                vrf = VRF.objects.filter(tenant=tenant).first()
            except Exception:
                pass
        
        if lan_ip:
            self._check_duplicate_ip(lan_ip, vrf)
        if wan_ip:
            self._check_duplicate_ip(wan_ip, vrf)
    
        if self.instance.pk:
            validation_device = self.instance
            validation_device.name = name
            validation_device.site = site
            validation_device.device_type = device_type
            validation_device.role = role
            validation_device.config_template = config_template
        else:
            validation_device = Device(
                name=name,
                site=site,
                device_type=device_type,
                role=role,
                config_template=config_template
            )
        try:
            validation_device.full_clean(exclude=['custom_field_data', 'local_context_data'])
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    raise forms.ValidationError(field, error)


        service = cleaned_data.get('Services')
        device_type = cleaned_data.get('device_type')
        service_required_fields = {
            'capn': ['CAPN_Address', 'Given_WAN_Address'],
            'internet': ['Given_WAN_Address'],  
            'isop': ['Given_WAN_Address'],
            'wan_failover': ['Given_WAN_Address'],
            'nkdps': ['Given_WAN_Address'],
            'lte_5g_nokia': []
        }

        all_conditional_fields = {'CAPN_Address','Given_WAN_Address'}
        
        required_fields = service_required_fields.get(service, [])
        
        for field_name in required_fields:
            field_value = cleaned_data.get(field_name)
            if not field_value:
                field_label = self.fields[field_name].label or field_name
                raise forms.ValidationError('{field_label} is required when {service} service is selected.')
        
        for field_name in all_conditional_fields:
            if field_name not in required_fields:
                if field_name in self.errors:
                    del self.errors[field_name]
                cleaned_data[field_name] = ''
                
        return cleaned_data

    def save(self, commit=True): 
        device = super().save(commit=False)
        
        if not device.config_template:
            auto_template = self._get_auto_config_template()
            if auto_template:
                device.config_template = auto_template

        if commit:
            device.save()
            
            enable_dhcp = self.cleaned_data.get('Enable_DHCP', False)
            dhcp_start = self.cleaned_data.get('DHCP_Start_Address', '') if enable_dhcp else ''
            dhcp_end = self.cleaned_data.get('DHCP_End_Address', '') if enable_dhcp else ''
            
            if not device.local_context_data:
                device.local_context_data = {}

            device.local_context_data['KAK_DATA'] = {
                'services': self.cleaned_data.get('Services', ''),
                'wan': self.cleaned_data.get('Given_WAN_Address', ''),
                'lan': self.cleaned_data.get('LAN_IP_Address_And_Subnet_Mask', ''),
                'service_id': self.cleaned_data.get('Service_ID', ''),
                'capn': self.cleaned_data.get('CAPN_Address', ''),
                'enable_dhcp': enable_dhcp,
                'dhcp_start': dhcp_start,
                'dhcp_end': dhcp_end
            }

            if not device.custom_field_data:
                device.custom_field_data = {}
            
            device.custom_field_data['PID'] = self.cleaned_data.get('Service_ID', '')
            device.save()
            service = device.local_context_data.get('KAK_DATA', {}).get('services', '')
            new_device_type = self.cleaned_data.get('device_type')
            if service!=self._original_service or new_device_type!=self._original_device_type:
                self._create_interfaces_from_config(device)

        return device

    def _create_interfaces_from_config(self, device):
        try:
            service = device.local_context_data.get('KAK_DATA', {}).get('services', '')
            if not service:
                logger.warning(f"No service defined for {device.name}")
                return
            device.interfaces.all().delete()
        
            interfaces_to_create = self._get_default_interfaces_for_service(service, device)
            logger.info(f"Creating {len(interfaces_to_create)} interfaces for service: {service}")

            vrf = self._get_vrf_for_device(device)
            interface_map = {}
            primary_ip_obj = None

            for iface_data in interfaces_to_create:
                try:
                    interface = Interface.objects.create(
                        device=device,
                        name=iface_data['name'],
                        type=iface_data['type'],
                        enabled=iface_data.get('enabled', True),
                        description=iface_data.get('description', ''),
                    )
                    interface_map[iface_data['name']] = interface

                    if iface_data.get('ip'):
                        ip_obj, created = IPAddress.objects.get_or_create(
                            address=iface_data['ip'],
                            vrf=vrf,
                            tenant=device.tenant,
                            defaults={'status': 'active'}
                        )
                        ip_obj.assigned_object = interface
                        ip_obj.save()
                        
                        if iface_data.get('is_primary'):
                            primary_ip_obj = ip_obj

                except Exception as e:
                    logger.error(f"Error creating interface {iface_data['name']}: {e}", exc_info=True)

            
            for iface_data in interfaces_to_create:
                if iface_data.get('lag'):
                    try:
                        child_interface = interface_map.get(iface_data['name'])
                        lag_interface = interface_map.get(iface_data['lag'])

                        if child_interface and lag_interface:
                            child_interface.lag = lag_interface
                            child_interface.save()
                            logger.info(f"Assigned {iface_data['name']} to LAG {iface_data['lag']}")
                        else:
                            logger.error(f"LAG assignment failed for {iface_data['name']}")
                    except Exception as e:
                        logger.error(f"Error assigning LAG for {iface_data['name']}: {e}", exc_info=True)

            for iface_data in interfaces_to_create:
                if iface_data.get('bridge'):
                    try:
                        child_interface = interface_map.get(iface_data['name'])
                        lag_interface = interface_map.get(iface_data['bridge'])

                        if child_interface and lag_interface:
                            child_interface.bridge = lag_interface
                            child_interface.save()
                            logger.info(f"Assigned {iface_data['name']} to Bridge {iface_data['bridge']}")
                        else:
                            logger.error(f"Bridge assignment failed for {iface_data['name']}")
                    except Exception as e:
                        logger.error(f"Error assigning Bridge for {iface_data['name']}: {e}", exc_info=True)


            for iface_data in interfaces_to_create:
                if iface_data.get('parent'):
                    try:
                        child_interface = interface_map.get(iface_data['name'])
                        parent_interface = interface_map.get(iface_data['parent'])

                        if child_interface and parent_interface:
                            child_interface.parent = parent_interface
                            child_interface.save()
                            logger.info(f"Assigned {iface_data['name']} to parent {iface_data['parent']}")
                        else:
                            logger.error(f"Parent assignment failed for {iface_data['name']}")
                    except Exception as e:
                        logger.error(f"Error assigning parent for {iface_data['name']}: {e}", exc_info=True)

            Device.objects.filter(pk=device.pk).update(
                primary_ip4=primary_ip_obj if primary_ip_obj else None
            )
            if primary_ip_obj:
                logger.info(f"Set primary IP: {primary_ip_obj.address}")

        except Exception as e:
            logger.error(f"Failed to create interfaces for {device.name}: {e}", exc_info=True)

    def _calculate_first_host(self, ip_address, subnet_mask=29):
        if not ip_address:
            return None
        try:
            network = ipaddress.ip_network(f"{ip_address}/{subnet_mask}", strict=False)
            return str(network.network_address + 3)
        except ValueError:
            return None

    def _wan_ip_60f_nkdps(self, given_wan_ip):
        if not given_wan_ip:
            return None
        try:
            network = ipaddress.ip_network(f"{given_wan_ip}/30", strict=False)
            return str(network.network_address + 2)
        except ValueError:
            return None

    def _calculate_wan_and_bgp_ip(self, given_wan_ip: str) -> str:
        if not given_wan_ip:
            return None
        try:
            network = ipaddress.ip_network(f"{given_wan_ip}/30", strict=False)
            return str(network.network_address + 2)
        except ValueError:
            return None


    def _get_default_interfaces_for_service(self, service, device):

        device_model = device.device_type.model.lower() if device.device_type else ''
        kak_data = device.local_context_data.get('KAK_DATA', {})
        wan_ip = kak_data.get('wan', '')
        lan_ip = kak_data.get('lan', '')
        calculated_wan_ip = self._calculate_first_host(wan_ip, 29)
        calculated_wan_and_bgp_ip = self._calculate_wan_and_bgp_ip(wan_ip)
        wan_ip_60f_nkdps = self._wan_ip_60f_nkdps(wan_ip)
        interfaces = []
        if service == 'capn':
            if 'd53g' in device_model:
                interfaces = [
                {'name': 'bridge1', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                {'name': 'lte1', 'type': 'lte', 'enabled': True, 'ip': wan_ip}, 
                {'name': 'ether1', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True}, 
                {'name': 'ether2', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},  
                {'name': 'ether3', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},
                {'name': 'ether4', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},  
                {'name': 'wlan1', 'type': 'virtual', 'enabled': True},
                {'name': 'wlan2', 'type': 'virtual', 'enabled': True},
                ]
    
        elif service == 'internet':
            if '50g' in device_model:
                interfaces = [
                    {'name': 'wan', 'type': '1000base-t', 'enabled': True, 'ip':  f'{wan_ip}/24'},
                    {'name': 'lan', 'type': '1000base-t', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'lan1', 'type': '1000base-t', 'enabled': True, 'parent': 'lan'},
                    {'name': 'lan2', 'type': '1000base-t', 'enabled': True, 'parent': 'lan'},
                    {'name': 'lan3', 'type': '1000base-t', 'enabled': True, 'parent': 'lan'},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True},
                ]
            elif '60f' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True, 'ip': f'{wan_ip}/24'},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True, 'description': 'WAN interface (DHCP)'},
                    {'name': 'dmz', 'type': '1000base-t', 'enabled': True, 'description': 'Default: 10.10.10.1'},
                    {'name': 'internal', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                ]
            elif '90g' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True, 'ip': f'{wan_ip}/29'},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True, 'description': 'WAN interface (DHCP)'},
                    {'name': 'lan', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'port1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port6', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                ]
        elif service == 'isop':
            if '60f' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'dmz', 'type': '1000base-t', 'enabled': True, 'description': 'Default: 10.10.10.1'},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                    {'name': 'internal', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'wans1.isop', 'type': 'bridge', 'enabled': True, 'ip': f'{calculated_wan_ip}/29'},
                
                ]
            elif '90g' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port6', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                    {'name': 'lan', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'wans1.isop', 'type': 'bridge', 'enabled': True, 'ip': calculated_wan_ip},
                
                ]
        elif service == 'lte_5g_nokia':
            if 'rb760igs capn' in device_model:
                interfaces = [
                    {'name': 'ether1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'bridge1', 'type': 'Bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'ether2', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},
                    {'name': 'ether3', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},  
                    {'name': 'ether4', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},
                    {'name': 'ether5', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},
                    {'name': 'serial0', 'type': 'other', 'enabled': True}, 
                ]
            elif 'fortigate 60f internet' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True, 'description': 'WAN interface (DHCP)'},
                    {'name': 'dmz', 'type': '1000base-t', 'enabled': True, 'description': 'Default: 10.10.10.1'},
                    {'name': 'internal', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                ]
        elif service == 'wan_failover':
            if '40f' in device_model:
                interfaces = [
                    {'name': 'wan', 'type': '1000base-t', 'enabled': True, 'ip': f'{wan_ip}/24'},
                    {'name': 'lan1', 'type': '1000base-t', 'enabled': True, 'parent': 'interval'},
                    {'name': 'lan2', 'type': '1000base-t', 'enabled': True, 'parent': 'interval'},
                    {'name': 'lan3', 'type': '1000base-t', 'enabled': True, 'parent': 'interval'},
                    {'name': 'wwan', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'loop', 'type': 'virtual', 'enabled': True},
                    {'name': 'interval', 'type': 'virtual', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                ]
            elif 'd53g' in device_model:
                interfaces = [
                    {'name': 'ether1', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},
                    {'name': 'bridge1', 'type': 'Bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'ether2', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},
                    {'name': 'ether3', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},  
                    {'name': 'ether4', 'type': '1000base-t', 'enabled': True,'bridge': 'bridge1'},
                    {'name': 'wan-ether5', 'type': '1000base-t', 'enabled': True, 'ip': f'{wan_ip}/24'},
                    {'name': 'lte1-wan', 'type': 'lte', 'enabled': True}, 
                    ]
        elif service == 'nkdps':
            if '921' in device_model:
                interfaces = [
                    {'name': 'GigabitEthernet0', 'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet4.4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet5', 'type': '1000base-t', 'enabled': True,'ip': f'{calculated_wan_and_bgp_ip}/24',  'is_primary': True},
                    {'name': 'Vlan1', 'type': '1000base-t', 'enabled': True, 'ip': lan_ip},
                ]

            elif '60f' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'dmz', 'type': '1000base-t', 'enabled': True, 'description': 'Default: 10.10.10.1'},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                    {'name': 'internal', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'MPLS_WAN', 'type': 'bridge', 'enabled': True, 'ip': f'{wan_ip_60f_nkdps}/24'},
                ]
            elif '90g' in device_model:
                interfaces = [
                    {'name': 'wan1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'port6', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a', 'type': '1000base-t', 'enabled': True},
                    {'name': 'b', 'type': '1000base-t', 'enabled': True},
                    {'name': 'modem', 'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual', 'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual', 'enabled': True, 'description':'SSL VPN interface'},
                    {'name': 'lan', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'MPLS_WAN', 'type': 'bridge', 'enabled': True, 'ip': f'{wan_ip_60f_nkdps}/24'},
                ]
            elif 'rb760igs' in device_model:
                interfaces = [
                    {'name': 'ether1',  'type': '1000base-t', 'enabled': True}, 
                    {'name': 'ether2', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},  
                    {'name': 'ether3', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'ether4', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},  
                    {'name': 'ether5', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'bridge1', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'VLAN4_WAN', 'type': 'virtual', 'enabled': True, 'ip': f'{wan_ip}/24'}, 
                ]
            elif 'rb4011igs' in device_model:
                interfaces = [
                    {'name': 'bridge1', 'type': 'bridge', 'enabled': True, 'ip': lan_ip, 'is_primary': True},
                    {'name': 'serial0', 'type': 'other', 'enabled': True},
                    {'name': 'serial1', 'type': 'other', 'enabled': True},
                    {'name': 'VLAN4_WAN', 'type': 'virtual', 'enabled': True, 'ip': f'{wan_ip}/24'}, 
                    {'name': 'ether1', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'ether2', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},  
                    {'name': 'ether3', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'ether4', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},  
                    {'name': 'ether5', 'bridge': 'bridge1', 'type': '1000base-t', 'enabled': True},
                ]
        return interfaces


    def _get_vrf_for_device(self, device):
        if device.tenant:
            return VRF.objects.filter(tenant=device.tenant).first()
        return None
    



class NewSiteForm(SiteForm):
    class Meta:
        model = Site
        fields = ['name', 'slug', 'status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_fields = ['name', 'slug', 'status']
        for field_name in list(self.fields.keys()):
            if field_name not in allowed_fields:
                del self.fields[field_name]



class NewTenantForm(TenantForm):
    class Meta:
        model = Tenant
        fields = ['name', 'slug']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_fields = ['name', 'slug']

        for field_name in list(self.fields.keys()):
            if field_name not in allowed_fields:
                del self.fields[field_name]
      
        if hasattr(self, 'custom_field_groups'):
            cleaned_groups = {}
            for group, fields in self.custom_field_groups.items():
                remaining_fields = [f for f in fields if f in self.fields]
                if remaining_fields:
                    cleaned_groups[group] = remaining_fields
            self.custom_field_groups = cleaned_groups
        
        if hasattr(self, 'nullable_fields'):
            self.nullable_fields = [f for f in self.nullable_fields if f in self.fields]
    
    def _get_cpe_group(self):
        try:
            return TenantGroup.objects.get(name="CPE")
        except TenantGroup.DoesNotExist:
            return None
    
    def clean(self):
        cleaned_data = super().clean()
        slug = self.data.get('slug')
        cpe_group = self._get_cpe_group()
        if not cpe_group:
            return cleaned_data

        if slug:
            try:
                cpe_group = TenantGroup.objects.get(name='CPE')
                slug_existing_tenant = Tenant.objects.filter(group=cpe_group, slug=slug)
                
                if self.instance.pk:
                    slug_existing_tenant = slug_existing_tenant.exclude(pk=self.instance.pk)
                
                if slug_existing_tenant.exists():
                    raise forms.ValidationError('Tenant slug must be unique per group.')
            except TenantGroup.DoesNotExist:
                pass

        name = self.data.get('name')
        if name:
            try:
                cpe_group = TenantGroup.objects.get(name='CPE')
                name_existing_tenant = Tenant.objects.filter(group=cpe_group, name=name)
                
                if self.instance.pk:
                    name_existing_tenant = name_existing_tenant.exclude(pk=self.instance.pk)
                
                if name_existing_tenant.exists():
                    raise forms.ValidationError('Tenant name must be unique per group.')
            except TenantGroup.DoesNotExist:
                pass
        
        return cleaned_data

        
    def save(self, commit=True):
            tenant = super().save(commit=False)
            cpe_group = self._get_cpe_group()

            if cpe_group:
                tenant.group = cpe_group

            if commit:
                tenant.save()
                if cpe_group:
                    vrf_name = f"vrf-{cpe_group.name.lower()}-{tenant.name.lower()}-default"
                    VRF.objects.get_or_create(
                        name=vrf_name,
                        defaults={"tenant": tenant},
                    )

            return tenant