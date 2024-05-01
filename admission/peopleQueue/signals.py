from django.dispatch import receiver
from django.db.models.signals import post_save
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import TalonLog
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


@receiver(post_save, sender=TalonLog)
async def on_talonlog_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    result = await schema.execute_async(talonlog_query, variables={'talonLog': instance}, context={'talonLog': instance})
    await channel_layer.group_send('tablo', {
        "type": 'talonLog.create',
        'message': result.data
    })
