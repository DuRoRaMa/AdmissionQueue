from django.db.models.signals import post_save
from django.dispatch import receiver

from . import max_tasks, models, tasks


@receiver(post_save, sender=models.HelpRequest)
def on_help_request_post_save(
    sender,
    instance,
    created,
    raw=False,
    using=None,
    update_fields=None,
    **kwargs,
) -> None:
    if raw or not created:
        return

    tasks.send_request_to_tg_chat.delay(instance.id)
    max_tasks.send_request_to_max.delay(instance.id)