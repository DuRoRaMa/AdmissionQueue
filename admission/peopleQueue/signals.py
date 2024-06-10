from datetime import timedelta
from django.dispatch import receiver
from django.db.models.signals import post_save
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
import django_rq
from rq import Queue
from .tasks import send_to_admin, send_to_tg_chat

from .models import OperatorLocation, TalonLog, Talon, OperatorQueue
from .schema import schema

channel_layer = get_channel_layer()

talonlog_query = """
query getTalonById($id: Int!) {
  talonLogById(id: $id) {
    id
    talon {
      id
      name
    }
    action
    createdBy {
      operatorSettings {
        location {
          name
        }
      }
    }
    createdAt
  }
}
"""


@receiver(post_save, sender=Talon)
async def on_talon_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    # if OQ exist then assing talon for this user
    # else ignore. For this talon doesnt exist suitable user
    if created:
        OQ = await OperatorQueue.objects.filter(purpose=instance.purpose).select_related('user').afirst()
        if OQ:
            user = OQ.user
            user.aassign_talon()
        send_to_admin.delay('Talon created', instance)


@receiver(post_save, sender=TalonLog)
async def on_talonlog_post_save(sender, instance: TalonLog, created: bool, raw, using, update_fields, **kwargs):
    result = await schema.execute_async(talonlog_query, variables={'id': instance.id}, is_awaitable=True)
    print(result)
    await channel_layer.group_send('tablo', {
        "type": 'talonLog.create',
        'message': result.data
    })
    talon = instance.talon
    if talon.tg_chat_id:
        minutes = 0
        text = ""
        if instance.action == TalonLog.Actions.ASSIGNED:
            # await instance.arefresh_from_db(fields=['created_by'])
            created_by = await get_user_model().objects.select_related(
                'operator_settings'
            ).aget(
                pk=instance.created_by.pk
            )
            operator_settings = created_by.operator_settings
            location = await OperatorLocation.objects.aget(
                settings=operator_settings.pk
            )
            text = f"""
            Статус талона {talon.name} обновлен!\nОператор ожидает вас за столом: {location.name}"""
        elif instance.action == TalonLog.Actions.CANCELLED:
            text = f"""
            Статус талона {talon.name} обновлен!\nК сожалению Ваш талон больше недействителен.\nЧтобы взять новый талон обратитесь, пожалуйста, на стойку ресепшена."""
        elif instance.action == TalonLog.Actions.COMPLETED:
            minutes = 5
            text = f"""
            Статус талона {talon.name} обновлен!\nСпасибо, что обратились в Приемную комиссию ДВФУ.\nСвой отзыв Вы можете оставить в меню "Мои талоны"""
        queue: Queue = django_rq.queues.get_queue()
        queue.enqueue_in(timedelta(minutes=minutes),
                         send_to_tg_chat,
                         talon.tg_chat_id, text)
        # send_to_tg_chat.delay(talon.tg_chat_id, text)
