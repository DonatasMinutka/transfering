from netbox.views import generic
from dcim.models import Device, Site
from tenancy.models import Tenant
from . import forms


class KakDeviceEditView(generic.ObjectEditView):
    queryset = Device.objects.all()
    form = forms.CustomDeviceForm


class KakSiteCreateView(generic.ObjectEditView):
    queryset = Site.objects.all()
    form = forms.NewSiteForm
    template_name = 'kak_form/add_site.html'

class KakSiteCreateView(generic.ObjectEditView):
    queryset = Site.objects.all()
    form = forms.NewSiteForm
    template_name = 'kak_form/edit_site.html'



class KakTenantCreateView(generic.ObjectEditView):
    queryset = Tenant.objects.all()
    form = forms.NewTenantForm
    template_name = 'kak_form/add_tenant.html'


