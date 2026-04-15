from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from dcim.forms import SiteForm
from tenancy.forms import TenantForm
from tenancy.models import Tenant
from django.contrib.contenttypes.models import ContentType
from dcim.models import Device, DeviceType, DeviceRole, Interface, Site
from extras.models import ConfigTemplate
from utilities.forms.fields import DynamicModelChoiceField
from ipam.models import IPAddress, VRF
import ipaddress
from tenancy.models import TenantGroup
import logging
from extras.models import Tag


logger = logging.getLogger(__name__)


def validate_ipv4(value):
    if value:
        try:
            ipaddress.IPv4Address(value)
        except ValueError:
            raise ValidationError('Enter a valid IPv4 address (e.g., 192.168.1.1)')


def validate_ipv4_cidr(value):
    if value:
        if '/' not in value:
            raise ValidationError('Enter valid IP with CIDR notation (e.g., 192.168.1.0/32)')
        try:
            ipaddress.IPv4Network(value, strict=False)
        except ValueError:
            raise ValidationError('Enter valid IP with CIDR notation (e.g., 192.168.1.0/32)')



class CustomDeviceForm(forms.ModelForm):
    SERVICE_CHOICES = [
        ('', '--- Select Service ---'),
        ('capn', 'CAPN'),
        ('internet', 'Internet'),
        ('isop', 'ISOP'),
        ('nkdps', 'NKDPS'),
        ('wan_failover', 'WAN FAILOVER'),
        ('lte_5g_nokia', 'LTE 5G From Nokia'),
        ('4g', '4G'),
        ('4g_apn', '4G APN'),
    ]

    Services = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        required=True,
        label="Services / Paslaugos",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    Given_WAN_Address = forms.CharField(
        max_length=50,
        required=False,
        validators=[validate_ipv4_cidr],
        widget=forms.TextInput(attrs={'placeholder': '192.168.1.1', 'class': 'form-control'}),
        label="WAN IP Address",
    )
    LAN_IP_Address_And_Subnet_Mask = forms.CharField(
        max_length=50,
        required=True,
        validators=[validate_ipv4_cidr],
        widget=forms.TextInput(attrs={
            'placeholder': '192.168.1.1/32',
            'class': 'form-control',
        }),
        label="LAN IP Address Ir Subnet",
    )
    Additional_LAN_IPs = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_additional_lan_ips'}),
        label="Additional LAN IPs",
    )
    Service_ID = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '********', 'class': 'form-control'}),
        label="PID",
    )
    Enable_DHCP = forms.BooleanField(
        required=False,
        label="Enable DHCP",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'enable_dhcp_checkbox'}),
    )
    DHCP_Ranges = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_dhcp_ranges'}),
        label="DHCP Ranges",
    )
    Enable_DHCP_HELPER = forms.BooleanField(
        required=False,
        label="Enable DHCP HELPER",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'enable_dhcp_helper_checkbox'}),
    )
    DHCP_HELPER = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_dhcp_helper',
            'class': 'form-control',
            'placeholder': '192.168.1.2, 192.168.2.4',
            'style': 'display:none;',
        }),
        label="",
    )
    CAPN_Address = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '192.168.1.1', 'class': 'form-control'}),
        label="CAPN Address",
    )
    Tunnel = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '192.168.1.1', 'class': 'form-control'}),
        label="Tunnel",
    )
    Cellular = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '192.168.1.1', 'class': 'form-control'}),
        label="Cellular",
    )

    class Meta:
        model = Device
        fields = ['name', 'role', 'device_type', 'tenant', 'site']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['device_type'] = DynamicModelChoiceField(
            queryset=DeviceType.objects.all(),
            query_params={'tag': '$Services'},
            required=True,
        )
        self.fields['name'].widget.attrs.update({
            'id': 'id_name',
            'class': 'form-control',
            'readonly': True,
            'style': 'background-color: #e9ecef; cursor: not-allowed;',
        })
        self.fields['name'].widget.attrs.update({'id': 'id_name', 'class': 'form-control'})
        self.fields['tenant'].label = 'Tenant / Imone'
        self.fields['tenant'].required = True
        self.fields['site'].label = 'Site / Vieta'
        self.fields['name'].label = 'Name / Pavadinimas (Sugeneruojamas)'
        self.fields['device_type'].label = 'Device Type / Modelis'
        self.fields['device_type'].widget.attrs['id'] = 'id_device_type'
        self.fields['device_type'].widget.attrs['data-custom-display'] = 'manufacturer-model'

        try:
            cpe_role = DeviceRole.objects.get(name='CPE')
            self.fields['role'].queryset = DeviceRole.objects.filter(name='CPE')
            self.fields['role'].initial = cpe_role
            self.fields['role'].empty_label = None
            self.fields['role'].widget.attrs.update({'class': 'hide-role-field'})
        except DeviceRole.DoesNotExist:
            pass

        self._original_service = None
        self._original_device_type = None
        self._original_lan = None
        self._original_wan = None
        if self.instance and self.instance.pk:
            kak_data = (self.instance.local_context_data or {}).get('KAK_DATA', {})
            self._original_service = kak_data.get('services', '')
            self._original_lan = kak_data.get('lan', '')
            self._original_wan = kak_data.get('wan', '')
            self._original_device_type = self.instance.device_type

        self.fields['name'].help_text = mark_safe(
            '<script src="/static/kak_form/js/auto_name.js"></script>'
        )
        self.fields['role'].help_text = mark_safe(
            '<link rel="stylesheet" href="/static/kak_form/css/custom.css">'
        )
        self.fields['device_type'].help_text = mark_safe(
            '<script src="/static/kak_form/js/device_type_display.js"></script>'
        )
        self.fields['site'].help_text = mark_safe(
            '<script src="/static/kak_form/js/site_refresh.js"></script>'
        )
        self.fields['tenant'].help_text = mark_safe(
            '<script src="/static/kak_form/js/tenant_refresh.js"></script>'
        )
        self.fields['Enable_DHCP'].help_text = mark_safe(
            '<script src="/static/kak_form/js/dhcp_toggle.js"></script>'
        )
        self.fields['Enable_DHCP_HELPER'].help_text = mark_safe(
            '<script src="/static/kak_form/js/dhcp_helper_toggle.js"></script>'
        )
        self.fields['Services'].help_text = mark_safe(
            '<script src="/static/kak_form/js/extra_fields.js"></script>'
        )
        self.fields['LAN_IP_Address_And_Subnet_Mask'].help_text = mark_safe(
            '<script src="/static/kak_form/js/multi_lan_ip.js"></script>'
        )

        self.order_fields(['name', 'role', 'Services', 'device_type', 'site'])

        if self.instance and self.instance.pk:
            kak_data = (self.instance.local_context_data or {}).get('KAK_DATA', {})
            self.fields['CAPN_Address'].initial = kak_data.get('capn', '')
            self.fields['Cellular'].initial = kak_data.get('cellular', '')
            self.fields['Tunnel'].initial = kak_data.get('tunnel', '')
            self.fields['Enable_DHCP'].initial = kak_data.get('enable_dhcp', False)
            self.fields['Enable_DHCP_HELPER'].initial = kak_data.get('enable_dhcp_helper', False)
            self.fields['Services'].initial = kak_data.get('services', '')
            self.fields['Given_WAN_Address'].initial = kak_data.get('wan', '')
            self.fields['LAN_IP_Address_And_Subnet_Mask'].initial = kak_data.get('lan', '')
            self.fields['Service_ID'].initial = kak_data.get('service_id', '')
            self.fields['DHCP_HELPER'].initial = kak_data.get('dhcp_helper', '')

            additional = kak_data.get('additional_lan_ips', [])
            self.fields['Additional_LAN_IPs'].initial = (
                ';'.join(additional) if isinstance(additional, list) else (additional or '')
            )

            dhcp_ranges = kak_data.get('dhcp_ranges', '')
            if isinstance(dhcp_ranges, list):
                dhcp_ranges = ';'.join(dhcp_ranges)
            if not dhcp_ranges:
                old_start = kak_data.get('dhcp_start', '')
                old_end = kak_data.get('dhcp_end', '')
                if old_start and old_end:
                    dhcp_ranges = f"{old_start}-{old_end}"
            self.fields['DHCP_Ranges'].initial = dhcp_ranges


    def _get_auto_config_template(self):
        device = self.instance
        service = self.data.get('Services')
        if device.pk:
            device_type = device.device_type
        else:
            device_type_id = self.data.get('device_type')
            try:
                device_type = DeviceType.objects.get(pk=device_type_id) if device_type_id else None
            except (DeviceType.DoesNotExist, ValueError):
                return None
        if not device_type or not service or not device_type.manufacturer:
            return None
        search_name = f"{device_type.manufacturer}_{device_type.model}_{service}".replace(' ', '_')
        return ConfigTemplate.objects.filter(name__icontains=search_name).first()

    def _check_duplicate_ip(self, ip_address, vrf, extra_exclude_pks=None):
        interface_ct = ContentType.objects.get_for_model(Interface)

        qs = IPAddress.objects.filter(address=ip_address)

        if self.instance.pk:
            own_iface_ids = list(
                Interface.objects.filter(device_id=self.instance.pk).values_list('id', flat=True)
            )
            if own_iface_ids:
                qs = qs.exclude(
                    assigned_object_type=interface_ct,
                    assigned_object_id__in=own_iface_ids,
                )
            if extra_exclude_pks:
                qs = qs.exclude(pk__in=extra_exclude_pks)

        if qs.exists():
            existing = qs.first()
            vrf_name = existing.vrf.name if existing.vrf else 'No VRF'
            status = existing.status or 'unknown'
            raise forms.ValidationError(
                f"IP {ip_address} already exists in NetBox (VRF: {vrf_name}, status: {status}). "
                f"Please use a different address or free this IP first."
            )

    def _check_dhcp_range(self, lan_ip, dhcp_start, dhcp_end):
        if not all([lan_ip, dhcp_start, dhcp_end]):
            return False
        net = ipaddress.ip_network(lan_ip, strict=False)
        start = ipaddress.ip_address(dhcp_start)
        end = ipaddress.ip_address(dhcp_end)
        first_host = net.network_address + 1
        last_host = net.broadcast_address - 1
        return first_host <= start <= last_host and first_host <= end <= last_host

    def _parse_additional_lan_ips(self, raw):
        if not raw:
            return []
        return [ip.strip() for ip in raw.split(';') if ip.strip()]

    def clean(self):
        cleaned_data = super().clean()

        lan_ip = cleaned_data.get('LAN_IP_Address_And_Subnet_Mask')
        wan_ip = cleaned_data.get('Given_WAN_Address')
        service_id = cleaned_data.get('Service_ID')
        tenant = cleaned_data.get('tenant')
        name = cleaned_data.get('name')
        site = cleaned_data.get('site')
        device_type = cleaned_data.get('device_type')
        role = cleaned_data.get('role')
        config_template = cleaned_data.get('config_template')
        enable_dhcp = cleaned_data.get('Enable_DHCP')
        dhcp_ranges_str = cleaned_data.get('DHCP_Ranges', '')
        additional_lan_raw = cleaned_data.get('Additional_LAN_IPs', '')
        service_id = cleaned_data.get('Service_ID')
        if service_id:
            qs = Device.objects.filter(custom_field_data__PID=service_id)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A device with PID "{service_id}" already exists.')
        additional_lan_ips = self._parse_additional_lan_ips(additional_lan_raw)
        for ip_cidr in additional_lan_ips:
            if '/' not in ip_cidr:
                raise forms.ValidationError(
                    f"Additional LAN IP '{ip_cidr}' must include CIDR notation (e.g. 10.0.0.1/24)."
                )
            try:
                ipaddress.IPv4Network(ip_cidr, strict=False)
            except ValueError:
                raise forms.ValidationError(
                    f"Additional LAN IP '{ip_cidr}' is not a valid IPv4 CIDR address."
                )
        seen_additional = []
        for ip_cidr in additional_lan_ips:
            if ip_cidr in seen_additional:
                raise forms.ValidationError(
                    f"Additional LAN IP '{ip_cidr}' is listed more than once."
                )
            seen_additional.append(ip_cidr)
        cleaned_data['Additional_LAN_IPs'] = additional_lan_ips

        if enable_dhcp and dhcp_ranges_str:
            ranges = [r.strip() for r in dhcp_ranges_str.split(';') if r.strip()]
            if len(ranges) > 10:
                raise forms.ValidationError("A maximum of 10 DHCP ranges is allowed.")
            for rng in ranges:
                if '-' not in rng:
                    raise forms.ValidationError(
                        f"Invalid DHCP range format: '{rng}'. "
                        "Expected format: 192.168.1.100-192.168.1.200"
                    )
                start, end = (s.strip() for s in rng.split('-', 1))
                try:
                    ipaddress.IPv4Address(start)
                    ipaddress.IPv4Address(end)
                except ValueError:
                    raise forms.ValidationError(f"Invalid IP address in DHCP range: '{rng}'")
                if not self._check_dhcp_range(lan_ip, start, end):
                    raise forms.ValidationError(f"DHCP range '{rng}' is outside the LAN subnet.")

        if name:
            qs = Device.objects.filter(name=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A device with name "{name}" already exists.')

        def _host(cidr):
            """Return just the host part of a CIDR string, or the value as-is."""
            return cidr.split('/')[0] if cidr and '/' in cidr else (cidr or '')

        if lan_ip and wan_ip and _host(lan_ip) == _host(wan_ip):
            raise forms.ValidationError("WAN and LAN IP addresses cannot be the same.")
        
        service = cleaned_data.get('Services')
        if service == 'nkdps' and wan_ip:
            try:
                network = ipaddress.IPv4Network(wan_ip, strict=False)
                if network.prefixlen != 30:
                    raise forms.ValidationError(
                        f"NKDPS service requires the WAN IP address to use a /30 subnet "
                        f"(e.g. 192.168.1.1/30). You entered '{wan_ip}' which has /{network.prefixlen}."
                    )
            except ValueError:
                pass 
        if service == 'isop' and wan_ip:
            try:
                network = ipaddress.IPv4Network(wan_ip, strict=False)
                if network.prefixlen != 29:
                    raise forms.ValidationError(
                        f"ISOP service requires the WAN IP address to use a /29 subnet "
                        f"(e.g. 192.168.1.1/29). You entered '{wan_ip}' which has /{network.prefixlen}."
                    )
            except ValueError:
                pass 
        if service == 'internet' and wan_ip:
            try:
                network = ipaddress.IPv4Network(wan_ip, strict=False)
                if network.prefixlen != 24:
                    raise forms.ValidationError(
                        f"Internet service requires the WAN IP address to use a /24 subnet "
                        f"(e.g. 192.168.1.1/24). You entered '{wan_ip}' which has /{network.prefixlen}."
                    )
            except ValueError:
                pass 
        for extra_ip in additional_lan_ips:
            if lan_ip and _host(extra_ip) == _host(lan_ip):
                raise forms.ValidationError(
                    f"Additional LAN IP '{extra_ip}' is the same as the primary LAN IP."
                )
            if wan_ip and _host(extra_ip) == _host(wan_ip):
                raise forms.ValidationError(
                    f"Additional LAN IP '{extra_ip}' conflicts with the WAN IP."
                )
        
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

        existing_additional_pks = []
        if self.instance.pk:
            kak_data = (self.instance.local_context_data or {}).get('KAK_DATA', {})
            existing_additional_pks = kak_data.get('additional_lan_ip_pks', [])


        if lan_ip:
            self._check_duplicate_ip(lan_ip, vrf)
        if wan_ip:
            self._check_duplicate_ip(wan_ip, vrf)
        for extra_ip in additional_lan_ips:
            self._check_duplicate_ip(extra_ip, vrf, extra_exclude_pks=existing_additional_pks)

        capn_address = cleaned_data.get('CAPN_Address')
        if capn_address:
            self._check_duplicate_ip(capn_address, vrf)

        tunnel = cleaned_data.get('Tunnel')
        if tunnel:
            self._check_duplicate_ip(tunnel, vrf)

        cellular = cleaned_data.get('Cellular')
        if cellular:
            self._check_duplicate_ip(cellular, vrf)

        if self.instance.pk:
            validation_device = self.instance
            validation_device.name = name
            validation_device.site = site
            validation_device.device_type = device_type
            validation_device.role = role
            validation_device.config_template = config_template
        else:
            validation_device = Device(
                name=name, site=site, device_type=device_type,
                role=role, config_template=config_template,
            )
        try:
            validation_device.full_clean(exclude=['custom_field_data', 'local_context_data'])
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    raise forms.ValidationError(error)

        service = cleaned_data.get('Services')
        service_required_fields = {
            'capn':         ['CAPN_Address', 'Given_WAN_Address'],
            'internet':     ['Given_WAN_Address'],
            'isop':         ['Given_WAN_Address'],
            'wan_failover': ['Given_WAN_Address'],
            'nkdps':        ['Given_WAN_Address'],
            '4g_apn':       ['CAPN_Address', 'Given_WAN_Address', 'Tunnel', 'Cellular'],
            '4g':           ['Given_WAN_Address', 'Tunnel', 'Cellular'],
            'lte_5g_nokia': [],
        }
        all_conditional_fields = {'CAPN_Address', 'Given_WAN_Address', 'Tunnel', 'Cellular'}
        required_fields = service_required_fields.get(service, [])

        for field_name in required_fields:
            if not cleaned_data.get(field_name):
                field_label = self.fields[field_name].label or field_name
                raise forms.ValidationError(
                    f'{field_label} is required when {service} service is selected.'
                )
        for field_name in all_conditional_fields - set(required_fields):
            self.errors.pop(field_name, None)
            cleaned_data[field_name] = ''

        return cleaned_data

   
    def save(self, commit=True):
        device = super().save(commit=False)

        if not device.config_template:
            auto_template = self._get_auto_config_template()
            if auto_template:
                device.config_template = auto_template

        if not commit:
            return device
        service = self.data.get('Services')
        device.save()
        SERVICES_WITH_SLA = {
            'capn', 'internet', 'isop', 'nkdps',
            'wan_failover', 'lte_5g_nokia', '4g', '4g_apn',
        }

        try:
            sla_tag = Tag.objects.get(slug='sla0')
            kak_tag = Tag.objects.get(slug='kak-form')
            device.tags.add(kak_tag)

            if service in SERVICES_WITH_SLA:
                service_tag = Tag.objects.get(slug=service)
                device.tags.add(service_tag, sla_tag)




        except Tag.DoesNotExist:
            pass  
        enable_dhcp = self.cleaned_data.get('Enable_DHCP', False)
        dhcp_ranges_str = self.cleaned_data.get('DHCP_Ranges', '') if enable_dhcp else ''
        enable_dhcp_helper = self.cleaned_data.get('Enable_DHCP_HELPER', False)
        dhcp_helper_str = self.cleaned_data.get('DHCP_HELPER', '') if enable_dhcp_helper else ''
        additional_lan_ips = self.cleaned_data.get('Additional_LAN_IPs', [])

        vrf = self._get_vrf_for_device(device)

        if not device.local_context_data:
            device.local_context_data = {}
        old_pks = device.local_context_data.get('KAK_DATA', {}).get('additional_lan_ip_pks', [])
        if old_pks:
            IPAddress.objects.filter(pk__in=old_pks, assigned_object_id__isnull=True).delete()

        new_additional_pks = []
        for ip_cidr in additional_lan_ips:
            if not isinstance(ip_cidr, str) or '.' not in ip_cidr:
                logger.error(f"Skipping invalid additional LAN IP value: {ip_cidr!r}")
                continue
            try:
                ip_obj, _ = IPAddress.objects.get_or_create(
                    address=ip_cidr,
                    vrf=vrf,
                    tenant=device.tenant,
                    defaults={'status': 'active'},
                )
                new_additional_pks.append(int(ip_obj.pk))
            except Exception as e:
                logger.error(f"Failed to get_or_create IPAddress for {ip_cidr!r}: {e}")
                continue

        device.local_context_data['KAK_DATA'] = {
            'services':              self.cleaned_data.get('Services', ''),
            'wan':                   self.cleaned_data.get('Given_WAN_Address', ''),
            'lan':                   self.cleaned_data.get('LAN_IP_Address_And_Subnet_Mask', ''),
            'service_id':            self.cleaned_data.get('Service_ID', ''),
            'capn':                  self.cleaned_data.get('CAPN_Address', ''),
            'cellular':              self.cleaned_data.get('Cellular', ''),
            'tunnel':                self.cleaned_data.get('Tunnel', ''),
            'enable_dhcp':           enable_dhcp,
            'dhcp_ranges':           [r.strip() for r in dhcp_ranges_str.split(';') if r.strip()] if dhcp_ranges_str else [],
            'enable_dhcp_helper':    enable_dhcp_helper,
            'dhcp_helper':           dhcp_helper_str,
            'additional_lan_ips':    additional_lan_ips,
            'additional_lan_ip_pks': new_additional_pks,
        }

        if not device.custom_field_data:
            device.custom_field_data = {}


        if dhcp_ranges_str:
            short_parts = []
            for rng in dhcp_ranges_str.split(';'):
                rng = rng.strip()
                if '-' in rng:
                    start, end = rng.split('-', 1)
                    short_parts.append(
                        f"{start.strip().split('.')[-1]}-{end.strip().split('.')[-1]}"
                    )
            device.custom_field_data['DHCP'] = ', '.join(short_parts)
        else:
            device.custom_field_data['DHCP'] = ''

        device.save()
        Device.objects.filter(pk=device.pk).update(
            custom_field_data={**device.custom_field_data, 'PID': self.cleaned_data.get('Service_ID', '')}
        )
        new_service     = device.local_context_data['KAK_DATA']['services']
        new_device_type = self.cleaned_data.get('device_type')
        new_lan         = self.cleaned_data.get('LAN_IP_Address_And_Subnet_Mask', '')
        new_wan         = self.cleaned_data.get('Given_WAN_Address', '')

        if (
            new_service        != self._original_service
            or new_device_type != self._original_device_type
            or new_lan         != self._original_lan
            or new_wan         != self._original_wan
        ):
            self._create_interfaces_from_config(device)

        device.refresh_from_db()

        if not device.custom_field_data:
            device.custom_field_data = {}

        lan_ip_str = self.cleaned_data.get('LAN_IP_Address_And_Subnet_Mask', '')
        lan_ip_obj = IPAddress.objects.filter(address=lan_ip_str).first() if lan_ip_str else None
        ip_obj = IPAddress.objects.filter(address=lan_ip_str).first() if lan_ip_str else None
        device.custom_field_data['DHCP_Helper']      = dhcp_helper_str
        device.custom_field_data['LAN_IP']           = int(lan_ip_obj.pk) if lan_ip_obj else None
        device.custom_field_data['Additional_LAN_IP'] = new_additional_pks
        device.custom_field_data['PID']              = self.cleaned_data.get('Service_ID', '')


        device.save()
        return device

    def _create_interfaces_from_config(self, device):
        try:
            kak_data = device.local_context_data.get('KAK_DATA', {})
            service  = kak_data.get('services', '')
            if not service:
                logger.warning(f"No service defined for {device.name}")
                return

            device.interfaces.all().delete()
            interfaces_to_create = self._get_default_interfaces_for_service(service, device)
            logger.info(f"Creating {len(interfaces_to_create)} interfaces for service: {service}")

            vrf            = self._get_vrf_for_device(device)
            interface_map  = {}
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
                        ip_obj, _ = IPAddress.objects.get_or_create(
                            address=iface_data['ip'],
                            vrf=vrf,
                            tenant=device.tenant,
                            defaults={'status': 'active'},
                        )
                        ip_obj.assigned_object = interface
                        ip_obj.save()
                        if iface_data.get('is_primary'):
                            primary_ip_obj = ip_obj
                except Exception as e:
                    logger.error(f"Error creating interface {iface_data['name']}: {e}", exc_info=True)

            for rel_key in ('lag', 'bridge', 'parent'):
                for iface_data in interfaces_to_create:
                    target_name = iface_data.get(rel_key)
                    if not target_name:
                        continue
                    child  = interface_map.get(iface_data['name'])
                    target = interface_map.get(target_name)
                    if child and target:
                        try:
                            setattr(child, rel_key, target)
                            child.save()
                            logger.info(f"Assigned {iface_data['name']} -> {rel_key.upper()} {target_name}")
                        except Exception as e:
                            logger.error(f"Error assigning {rel_key} for {iface_data['name']}: {e}", exc_info=True)
                    else:
                        logger.error(f"{rel_key.upper()} assignment failed: {iface_data['name']} -> {target_name}")

            Device.objects.filter(pk=device.pk).update(
                primary_ip4=primary_ip_obj if primary_ip_obj else None
            )
            if primary_ip_obj:
                logger.info(f"Set primary IP: {primary_ip_obj.address}")

        except Exception as e:
            logger.error(f"Failed to create interfaces for {device.name}: {e}", exc_info=True)

    def _calculate_first_host(self, given_wan_ip):
        if not given_wan_ip:
            return None
        try:
            network = ipaddress.ip_network(f"{given_wan_ip}", strict=False)

            if network.prefixlen != 29:
                raise ValueError(f"Expected /29, got /{network.prefixlen}")
            
            host_ip = network.network_address + 3         
            return f"{host_ip}/{network.prefixlen}"  
        except ValueError:
            return None
        
    def _calculate_wan_ip_from_30(self, given_wan_ip):
        if not given_wan_ip:
            return None
        try:
            network = ipaddress.ip_network(given_wan_ip, strict=False)

            if network.prefixlen != 30:
                raise ValueError(f"Expected /30, got /{network.prefixlen}")

            host_ip = network.network_address + 2  
            return f"{host_ip}/{network.prefixlen}"

        except ValueError as e:
            print(f"Invalid WAN IP: {e}")
            return None


    def _get_default_interfaces_for_service(self, service, device):
        device_model = device.device_type.model.lower() if device.device_type else ''
        kak_data = device.local_context_data.get('KAK_DATA', {})
        wan_ip   = kak_data.get('wan', '')
        lan_ip   = kak_data.get('lan', '')
        tunnel   = kak_data.get('tunnel', '')
        cellular = kak_data.get('cellular', '')

        calculated_wan_ip         = self._calculate_first_host(wan_ip)
        calculated_wan_ip_from_30 = self._calculate_wan_ip_from_30(wan_ip)

        interfaces = []

        if service == '4g':
            if 'c921-4pltegb' in device_model:
                interfaces = [
                    {'name': 'Tunnel0',           'type': 'virtual',    'enabled': True,  'ip': tunnel},
                    {'name': 'Cellular0',          'type': '4g',         'enabled': True,  'ip': cellular},
                    {'name': 'GigabitEthernet0',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet1',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet2',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet3',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet4',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet4.4', 'type': '1000base-t', 'enabled': True,  'ip': wan_ip},
                    {'name': 'GigabitEthernet5',   'type': '1000base-t', 'enabled': True},
                    {'name': 'Vlan1',              'type': '1000base-t', 'enabled': True,  'ip': lan_ip},
                ]

        elif service == '4g_apn':
            if 'd53g_apn' in device_model:
                interfaces = [
                    {'name': 'Tunnel0',  'type': 'virtual',    'enabled': True, 'ip': tunnel},
                    {'name': 'Cellular0','type': '4g',          'enabled': True, 'ip': cellular},
                    {'name': 'bridge1',  'type': 'bridge',      'enabled': True, 'ip': lan_ip},
                    {'name': 'lte1',     'type': 'lte',         'enabled': True, 'ip': wan_ip, 'is_primary': True},
                    {'name': 'ether1',   'type': '1000base-t',  'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'ether2',   'type': '1000base-t',  'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'ether3',   'type': '1000base-t',  'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'ether4',   'type': '1000base-t',  'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'wlan1',    'type': 'virtual',     'enabled': True},
                    {'name': 'wlan2',    'type': 'virtual',     'enabled': True},
                ]

        elif service == 'capn':
            if 'd53g' in device_model:
                interfaces = [
                    {'name': 'bridge1', 'type': 'bridge',    'enabled': True, 'ip': lan_ip},
                    {'name': 'lte1',    'type': 'lte',        'enabled': True, 'ip': wan_ip, 'is_primary': True},
                    {'name': 'ether1',  'type': '1000base-t', 'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'ether2',  'type': '1000base-t', 'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'ether3',  'type': '1000base-t', 'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'ether4',  'type': '1000base-t', 'enabled': True, 'bridge': 'bridge1'},
                    {'name': 'wlan1',   'type': 'virtual',    'enabled': True},
                    {'name': 'wlan2',   'type': 'virtual',    'enabled': True},
                ]

        elif service == 'internet':
            if '50g' in device_model:
                interfaces = [
                    {'name': 'wan',      'type': '1000base-t', 'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                    {'name': 'lan',      'type': '1000base-t', 'enabled': True,  'ip': lan_ip},
                    {'name': 'lan1',     'type': '1000base-t', 'enabled': True,  'parent': 'lan'},
                    {'name': 'lan2',     'type': '1000base-t', 'enabled': True,  'parent': 'lan'},
                    {'name': 'lan3',     'type': '1000base-t', 'enabled': True,  'parent': 'lan'},
                    {'name': 'a',        'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',    'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual',    'enabled': True},
                ]
            elif '60f' in device_model:
                interfaces = [
                    {'name': 'wan1',      'type': '1000base-t', 'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                    {'name': 'wan2',      'type': '1000base-t', 'enabled': True,  'description': 'WAN interface (DHCP)'},
                    {'name': 'dmz',       'type': '1000base-t', 'enabled': True,  'description': 'Default: 10.10.10.1'},
                    {'name': 'internal',  'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a',         'type': '1000base-t', 'enabled': True},
                    {'name': 'b',         'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',     'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root',  'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root',  'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root',  'type': 'virtual',    'enabled': True,  'description': 'SSL VPN interface'},
                ]
            elif '90g' in device_model:
                interfaces = [
                    {'name': 'wan1',   'type': '1000base-t', 'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                    {'name': 'wan2',   'type': '1000base-t', 'enabled': True,  'description': 'WAN interface (DHCP)'},
                    {'name': 'lan',    'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'port1',  'type': '1000base-t', 'enabled': True},
                    {'name': 'port2',  'type': '1000base-t', 'enabled': True},
                    {'name': 'port3',  'type': '1000base-t', 'enabled': True},
                    {'name': 'port4',  'type': '1000base-t', 'enabled': True},
                    {'name': 'port5',  'type': '1000base-t', 'enabled': True},
                    {'name': 'port6',  'type': '1000base-t', 'enabled': True},
                    {'name': 'a',      'type': '1000base-t', 'enabled': True},
                    {'name': 'b',      'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',  'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual',  'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual',  'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual',  'enabled': True,  'description': 'SSL VPN interface'},
                ]

        elif service == 'isop':
            if '60f' in device_model:
                interfaces = [
                    {'name': 'wan1',       'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2',       'type': '1000base-t', 'enabled': True},
                    {'name': 'dmz',        'type': '1000base-t', 'enabled': True,  'description': 'Default: 10.10.10.1'},
                    {'name': 'internal1',  'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2',  'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3',  'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4',  'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5',  'type': '1000base-t', 'enabled': True},
                    {'name': 'a',          'type': '1000base-t', 'enabled': True},
                    {'name': 'b',          'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',      'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root',   'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root',   'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root',   'type': 'virtual',    'enabled': True,  'description': 'SSL VPN interface'},
                    {'name': 'internal',   'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'wans1.isop', 'type': 'bridge',     'enabled': True,  'ip': f'{calculated_wan_ip}', 'is_primary': True},
                ]
            elif '90g' in device_model:
                interfaces = [
                    {'name': 'wan1',       'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2',       'type': '1000base-t', 'enabled': True},
                    {'name': 'port1',      'type': '1000base-t', 'enabled': True},
                    {'name': 'port2',      'type': '1000base-t', 'enabled': True},
                    {'name': 'port3',      'type': '1000base-t', 'enabled': True},
                    {'name': 'port4',      'type': '1000base-t', 'enabled': True},
                    {'name': 'port5',      'type': '1000base-t', 'enabled': True},
                    {'name': 'port6',      'type': '1000base-t', 'enabled': True},
                    {'name': 'a',          'type': '1000base-t', 'enabled': True},
                    {'name': 'b',          'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',      'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root',   'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root',   'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root',   'type': 'virtual',    'enabled': True,  'description': 'SSL VPN interface'},
                    {'name': 'lan',        'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'wans1.isop', 'type': 'bridge',     'enabled': True,  'ip': calculated_wan_ip, 'is_primary': True},
                ]

        elif service == 'lte_5g_nokia':
            if 'rb760igs capn' in device_model:
                interfaces = [
                    {'name': 'ether1',  'type': '1000base-t', 'enabled': True},
                    {'name': 'bridge1', 'type': 'bridge',     'enabled': True,  'ip': lan_ip, 'is_primary': True},
                    {'name': 'ether2',  'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether3',  'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether4',  'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether5',  'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'serial0', 'type': 'other',      'enabled': True},
                ]
            elif '60f internet' in device_model:
                interfaces = [
                    {'name': 'wan1',      'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2',      'type': '1000base-t', 'enabled': True,  'description': 'WAN interface (DHCP)'},
                    {'name': 'dmz',       'type': '1000base-t', 'enabled': True,  'description': 'Default: 10.10.10.1'},
                    {'name': 'internal',  'type': 'bridge',     'enabled': True,  'ip': lan_ip, 'is_primary': True},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a',         'type': '1000base-t', 'enabled': True},
                    {'name': 'b',         'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',     'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root',  'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root',  'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root',  'type': 'virtual',    'enabled': True,  'description': 'SSL VPN interface'},
                ]

        elif service == 'wan_failover':
            if '40f' in device_model:
                interfaces = [
                    {'name': 'wan',      'type': '1000base-t', 'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                    {'name': 'interval', 'type': 'virtual',    'enabled': True,  'ip': lan_ip},
                    {'name': 'lan1',     'type': '1000base-t', 'enabled': True,  'parent': 'interval'},
                    {'name': 'lan2',     'type': '1000base-t', 'enabled': True,  'parent': 'interval'},
                    {'name': 'lan3',     'type': '1000base-t', 'enabled': True,  'parent': 'interval'},
                    {'name': 'wwan',     'type': '1000base-t', 'enabled': True},
                    {'name': 'a',        'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',    'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'loop',     'type': 'virtual',    'enabled': True},
                ]
            elif 'd53g' in device_model:
                interfaces = [
                    {'name': 'bridge1',    'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'ether1',     'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether2',     'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether3',     'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether4',     'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'wan-ether5', 'type': '1000base-t', 'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                    {'name': 'lte1-wan',   'type': 'lte',        'enabled': True},
                ]

        elif service == 'nkdps':
            if '921' in device_model:
                interfaces = [
                    {'name': 'GigabitEthernet0',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet1',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet2',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet3',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet4',   'type': '1000base-t', 'enabled': True},
                    {'name': 'GigabitEthernet4.4', 'type': '1000base-t', 'enabled': True, 'ip': f'{calculated_wan_ip_from_30}', 'is_primary': True},
                    {'name': 'GigabitEthernet5',   'type': '1000base-t', 'enabled': True},
                    {'name': 'Vlan1',              'type': '1000base-t', 'enabled': True, 'ip': lan_ip},
                ]
            elif '60f' in device_model:
                interfaces = [
                    {'name': 'wan1',      'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2',      'type': '1000base-t', 'enabled': True},
                    {'name': 'dmz',       'type': '1000base-t', 'enabled': True,  'description': 'Default: 10.10.10.1'},
                    {'name': 'internal1', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal2', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal3', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal4', 'type': '1000base-t', 'enabled': True},
                    {'name': 'internal5', 'type': '1000base-t', 'enabled': True},
                    {'name': 'a',         'type': '1000base-t', 'enabled': True},
                    {'name': 'b',         'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',     'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root',  'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root',  'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root',  'type': 'virtual',    'enabled': True,  'description': 'SSL VPN interface'},
                    {'name': 'internal',  'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'MPLS_WAN',  'type': 'bridge',     'enabled': True,  'ip': f'{calculated_wan_ip_from_30}', 'is_primary': True},
                ]
            elif '90g' in device_model:
                interfaces = [
                    {'name': 'wan1',     'type': '1000base-t', 'enabled': True},
                    {'name': 'wan2',     'type': '1000base-t', 'enabled': True},
                    {'name': 'port1',    'type': '1000base-t', 'enabled': True},
                    {'name': 'port2',    'type': '1000base-t', 'enabled': True},
                    {'name': 'port3',    'type': '1000base-t', 'enabled': True},
                    {'name': 'port4',    'type': '1000base-t', 'enabled': True},
                    {'name': 'port5',    'type': '1000base-t', 'enabled': True},
                    {'name': 'port6',    'type': '1000base-t', 'enabled': True},
                    {'name': 'a',        'type': '1000base-t', 'enabled': True},
                    {'name': 'b',        'type': '1000base-t', 'enabled': True},
                    {'name': 'modem',    'type': '1000base-t', 'enabled': False},
                    {'name': 'naf.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'l2t.root', 'type': 'virtual',    'enabled': True},
                    {'name': 'ssl.root', 'type': 'virtual',    'enabled': True,  'description': 'SSL VPN interface'},
                    {'name': 'lan',      'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'MPLS_WAN', 'type': 'bridge',     'enabled': True,  'ip': f'{calculated_wan_ip_from_30}', 'is_primary': True},
                ]
            elif 'rb760igs' in device_model:
                interfaces = [
                    {'name': 'ether1',    'type': '1000base-t', 'enabled': True},
                    {'name': 'ether2',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether3',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether4',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether5',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'bridge1',   'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'VLAN4_WAN', 'type': 'virtual',    'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                ]
            elif 'rb4011igs' in device_model:
                interfaces = [
                    {'name': 'bridge1',   'type': 'bridge',     'enabled': True,  'ip': lan_ip},
                    {'name': 'serial0',   'type': 'other',      'enabled': True},
                    {'name': 'serial1',   'type': 'other',      'enabled': True},
                    {'name': 'VLAN4_WAN', 'type': 'virtual',    'enabled': True,  'ip': f'{wan_ip}', 'is_primary': True},
                    {'name': 'ether1',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether2',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether3',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether4',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
                    {'name': 'ether5',    'type': '1000base-t', 'enabled': True,  'bridge': 'bridge1'},
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
        self.fields['name'].help_text = 'Užvadinimo struktūra (Gatvė g. namo nr, Miestas) Pvz. "J. Basanavičiaus g. 93, Kėdainiai"'
        allowed_fields = {'name', 'slug', 'status'}
        for field_name in list(self.fields.keys()):
            if field_name not in allowed_fields:
                del self.fields[field_name]
    def save(self, commit=True):
        site = super().save(commit=False)
        if commit:
            site.save()
            self.save_m2m() 
            kak_tag, _ = Tag.objects.get_or_create(slug='kak-form')
            site.tags.add(kak_tag)
        return site
    
class NewTenantForm(TenantForm):
    class Meta:
        model = Tenant
        fields = ['name', 'slug']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Užvadinimo pavyzdžiai: Maxima, UAB; SEB bankas, AB; Įmonės pavadinimas, UAB "
        allowed_fields = {'name', 'slug', 'cf_imones_kodas', 'cf_kliento_id', 'cf_kliento_kontaktinis_asmuo', 'cf_paslaugu_gavejo_id','cf_tsm_sdm',''}
        for field_name in list(self.fields.keys()):
            if field_name not in allowed_fields:
                del self.fields[field_name]

        if hasattr(self, 'custom_field_groups'):
            self.custom_field_groups = {
                group: [f for f in fields if f in self.fields]
                for group, fields in self.custom_field_groups.items()
                if any(f in self.fields for f in fields)
            }
        if hasattr(self, 'nullable_fields'):
            self.nullable_fields = [f for f in self.nullable_fields if f in self.fields]

    def _get_cpe_group(self):
        try:
            return TenantGroup.objects.get(name='DPS verslo klientai')
        except TenantGroup.DoesNotExist:
            return None

    def clean(self):
        cleaned_data = super().clean()
        cpe_group = self._get_cpe_group()
        if not cpe_group:
            return cleaned_data
        imones_kodas = self.data.get('cf_imones_kodas')

        if imones_kodas:
            if not str(imones_kodas).isdigit():
                self.add_error('cf_imones_kodas', 'Įmonės kodas tik skaitmenys')
            elif len(str(imones_kodas)) != 9:
                self.add_error('cf_imones_kodas', 'Įmonės kodas turi būti 9 skaičiai')

        slug = self.data.get('slug')
        name = self.data.get('name')

        if slug:
            qs = Tenant.objects.filter(group=cpe_group, slug=slug)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Tenant slug must be unique per group.')

        if name:
            qs = Tenant.objects.filter(group=cpe_group, name=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Tenant name must be unique per group.')

        return cleaned_data

    def save(self, commit=True):
        tenant = super().save(commit=False)
        cpe_group = self._get_cpe_group()
        
        if cpe_group:
            tenant.group = cpe_group
        
        if commit:
            tenant.save()  
            
            kak_tag = Tag.objects.get(slug='kak-form')
            tenant.tags.add(kak_tag)             
            vrf_name = f"vrf-{cpe_group.name.lower()}-{tenant.name.lower()}-default"
            if cpe_group:
                VRF.objects.get_or_create(
                    name=vrf_name,
                    defaults={"tenant": tenant},
                )
        
        return tenant