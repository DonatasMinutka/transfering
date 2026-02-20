from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='KAK Form',
    groups=(
        ('Devices', (
            PluginMenuItem(
                link='plugins:kak_form:kak_device_add',
                link_text='Add Device',
                permissions=['dcim.add_device']
            ),
        )),
    )
)