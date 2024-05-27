from django.dispatch import receiver
from django.db.models.signals import post_save
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from .models import TalonLog, Talon, OperatorQueue
from .schema import schema
from .serializers import TalonLogSerializer

channel_layer = get_channel_layer()

talonlog_query = """
{
  talonLog {
    id
    talon {
      id
      name
    }
    action {
      name
    }
    createdBy {
      id
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


@receiver(post_save, sender=TalonLog)
async def on_talonlog_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    result = await schema.execute_async(talonlog_query, variables={'talonLog': instance}, context={'talonLog': instance})
    await channel_layer.group_send('tablo', {
        "type": 'talonLog.create',
        'message': result.data
    })
