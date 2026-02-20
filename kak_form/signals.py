from django.db.models.signals import pre_save
from django.dispatch import receiver
from dcim.models import Device
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Device)
def preserve_plugin_data(sender, instance, **kwargs):
    if not instance.pk:
        return
    
    try:
        old_device = Device.objects.get(pk=instance.pk)
    
        old_fields = {k: v for k, v in (old_device.custom_field_data or {}).items() 
                      if k.startswith('kak_form_')}
        new_fields = {k: v for k, v in (instance.custom_field_data or {}).items() 
                      if k.startswith('kak_form_')}
        
        if old_fields and not new_fields:
            if not instance.custom_field_data:
                instance.custom_field_data = {}
            instance.custom_field_data.update(old_fields)
            logger.info(f"Restored {len(old_fields)} custom fields for {instance.name}")
        
        old_kak = old_device.local_context_data.get('KAK_DATA') if old_device.local_context_data else None
        new_kak = instance.local_context_data.get('KAK_DATA') if instance.local_context_data else None
        
        if old_kak and not new_kak:
            if not instance.local_context_data:
                instance.local_context_data = {}
            instance.local_context_data['KAK_DATA'] = old_kak
            logger.info(f"Restored KAK_DATA for {instance.name}")
            
    except Device.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error preserving plugin data: {e}")