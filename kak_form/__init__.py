from netbox.plugins import PluginConfig

class MyPluginConfig(PluginConfig):
    name = 'kak_form'
    verbose_name = 'KAK FORM'
    description = 'KAK FORM'
    version = '0.1.0'
    base_url = 'kak-Form'
    
    def ready(self):
        super().ready()
        from . import navigation
        from . import config_file_extension
        from . import signals

config = MyPluginConfig 