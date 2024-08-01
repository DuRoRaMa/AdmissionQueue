import django_rq
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from datetime import timedelta
from rq import Queue
from .tasks import send_to_tg_chat, send_to_tablo

from .models import OperatorLocation, TalonLog, TalonActions

channel_layer = get_channel_layer()


@receiver(post_save, sender=TalonLog)
async def on_talonlog_post_save(sender, instance: TalonLog, created: bool, raw, using, update_fields, **kwargs):
    queue: Queue = django_rq.queues.get_queue()
    queue.enqueue_in(
        timedelta(milliseconds=100),
        send_to_tablo,
        instance.pk
    )
    talon = instance.talon
    if talon.tg_chat_id:
        minutes = 0
        text = ""
        if instance.action == TalonActions.CREATED:
            return
        elif instance.action == TalonActions.ASSIGNED:
            # await instance.arefresh_from_db(fields=['created_by'])
            created_by = await get_user_model().objects.select_related(
                'operator_settings'
            ).aget(
                pk=instance.created_by.pk
            )
            operator_settings = created_by.operator_settings  # type: ignore
            location = await OperatorLocation.objects.aget(
                settings=operator_settings.pk
            )
            text = f"""
            Статус талона {talon.name} обновлен!\nОператор ожидает вас за столом {location.name}"""
        elif instance.action == TalonActions.CANCELLED:
            text = f"""
            Статус талона {talon.name} обновлен!\nК сожалению Ваш талон больше недействителен.\nЧтобы взять новый талон обратитесь, пожалуйста, на стойку ресепшена."""
        elif instance.action == TalonActions.COMPLETED:
            minutes = 5
            text = f"""
            Статус талона {talon.name} обновлен!\nСпасибо, что обратились в Приемную комиссию ДВФУ.\nСвой отзыв Вы можете оставить в меню "Мои талоны"""
        queue.enqueue_in(timedelta(minutes=minutes),
                         send_to_tg_chat,
                         talon.tg_chat_id, text)
