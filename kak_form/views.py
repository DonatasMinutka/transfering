from netbox.views import generic
from dcim.models import Device, Site
from tenancy.models import Tenant
from . import forms
from ipam.models import IPAddress

class KakDeviceEditView(generic.ObjectEditView):
    queryset = Device.objects.all()
    form = forms.CustomDeviceForm

class KakDeviceView(generic.ObjectView):
    queryset = Device.objects.all()
    template_name = 'kak_form/device_detail_custom.html' 
    def get_extra_context(self, request, instance):
            context = super().get_extra_context(request, instance)
            pks = instance.custom_field_data.get('Additional_LAN_IP', [])
            context['Additional_LAN_IP'] = IPAddress.objects.filter(pk__in=pks)
            return context

class DefaultDeviceView(generic.ObjectView):
    queryset = Device.objects.all()

    
class KakSiteCreateView(generic.ObjectEditView):
    queryset = Site.objects.all()
    form = forms.NewSiteForm
    template_name = 'kak_form/add_site.html'


class KakTenantCreateView(generic.ObjectEditView):
    queryset = Tenant.objects.all()
    form = forms.NewTenantForm
    template_name = 'kak_form/add_tenant.html'


