from django.dispatch import receiver
from django.db.models.signals import post_save
from . import models
from . import tasks


@receiver(post_save, sender=models.HelpRequest)
async def on_help_request_post_save(sender, instance, created, raw, using, update_fields, **kwargs) -> None:
    if created:
        tasks.send_request_to_tg_chat.delay(instance.id)
