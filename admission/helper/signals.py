from django.dispatch import receiver
from django.db.models.signals import post_save

from . import models
from . import tasks
from . import max_tasks


@receiver(post_save, sender=models.HelpRequest)
def on_help_request_post_save(
    sender,
    instance,
    created,
    raw,
    using,
    update_fields,
    **kwargs,
) -> None:
    if raw or not created:
        return

    tasks.send_request_to_tg_chat.delay(instance.id)
    max_tasks.send_request_to_max.delay(instance.id)