from netbox.plugins import PluginTemplateExtension

class DeviceListButtons(PluginTemplateExtension):
    def list_buttons(self):
        request = self.context.get('request')
        if not request:
            return ''
        if request.resolver_match.view_name != 'dcim:device_list':
            return ''

        return self.render('kak_form/device_list_button.html')


class DeviceDetailButtons(PluginTemplateExtension):
    def buttons(self):
        request = self.context.get('request')
        if not request:
            return ''
    
        if request.resolver_match.view_name != 'dcim:device':
            return ''
            
        device = self.context['object']
        return self.render('kak_form/device_detail_button.html', extra_context={
            'device': device
        })

class DeviceMyPluginInfo(PluginTemplateExtension):
    def right_page(self):
        request = self.context.get('request')
        if not request:
            return ''
        
        if request.resolver_match.view_name != 'dcim:device':
            return ''
        
        device = self.context['object']
        return self.render('kak_form/device_info_panel.html', extra_context={
            'device': device
        })

template_extensions = [DeviceListButtons, DeviceDetailButtons, DeviceMyPluginInfo]