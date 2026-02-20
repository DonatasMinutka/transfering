from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from dcim.models import Device
import dcim.views

original_get = dcim.views.DeviceRenderConfigView.get
def custom_render_config_get(self, request, **kwargs):
    if request.GET.get('export'):
        pk = kwargs.get('pk')
        device = get_object_or_404(Device, pk=pk)
        
        if not device.config_template:
            return HttpResponse("No configuration template assigned to this device.", status=404)
        
        try:
            config_content = device.config_template.render(context={'device': device})
        except Exception as e:
            return HttpResponse(f"Error rendering config: {str(e)}", status=500)
        
        if not config_content:
            return HttpResponse("Configuration template rendered empty content.", status=404)

        extension = 'txt'
        if device.device_type and device.device_type.manufacturer:
            manufacturer = device.device_type.manufacturer.name.lower()
            
            extension_map = {
                'cisco': 'wri',
                'fortinet': 'conf',
                'mikrotik': 'rsc',
                'huawei': 'cfg',
            }

 
            extension = extension_map.get(manufacturer, 'txt')
        
        filename = f"{device.name}.{extension}"
        response = HttpResponse(config_content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    else:
        return original_get(self, request, **kwargs)

dcim.views.DeviceRenderConfigView.get = custom_render_config_get