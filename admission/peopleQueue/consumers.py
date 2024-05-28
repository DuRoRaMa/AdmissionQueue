from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .schema import schema

connect_query = """
query tabloStatus {
  talons {
    id
    name
    logs {
      id
      action
      createdAt
    }
  }
  talonLog {
    id
  }
}
"""


class AsyncTabloConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tablo']

    async def connect(self):
        result = await database_sync_to_async(
            lambda: schema.execute(connect_query))()
        await self.accept()
        await self.send_json({
            "type": "tablo.status",
            "message": result.data
        })

    async def disconnect(self, close_code):
        pass

    async def talonLog_create(self, event):
        message = event['message']
        # await self.send_json({
        #     "type": event['type'],
        #     "message": result.data
        # })
        # await self.send_json({
        #     "type": event['type'],
        #     "message": self.scope.get('test', 'NOope')
        # })
        await self.send_json({
            "type": event['type'],
            "message": message
        })

    # async def receive(self, text_data):
    #     text_data_json = await self.decode_json(text_data)
    #     message = text_data_json['message']
    #     # Отправка сообщения всем участникам группы
    #     await self.channel_layer.group_send(
    #         "tablo", {
    #             "type": "chat_message",
    #             "message": self.scope['user'].username+" hui"
    #         }
    #     )

    # async def talon_create(self, event):
    #     message = event['message']
    #     await self.send_json({
    #             "type": event['type'],
    #             "message": message
    #         })

    # async def talon_update(self, event):
    #     message = event['message']
    #     await self.send_json({
    #             "type": event['type'],
    #             "message": message
    #         })

    # async def talon_remove(self, event):
    #     message = event['message']
    #     await self.send_json({
    #             "type": event['type'],
    #             "message": message
    #         })
