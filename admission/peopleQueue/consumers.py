from channels.generic.websocket import AsyncJsonWebsocketConsumer

class AsyncTabloConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tablo']
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = await self.decode_json(text_data)
        message = text_data_json['message']
        # Отправка сообщения всем участникам группы
        await self.channel_layer.group_send(
            "tablo", {
                "type": "chat_message",  
                "message": self.scope['user'].username+" hui"
            }
        )

    async def talon_create(self, event):
        message = event['message']
        await self.send_json({
                "type": event['type'],
                "message": message
            })

    async def talon_update(self, event):
        message = event['message']
        await self.send_json({
                "type": event['type'],
                "message": message
            })

    async def talon_remove(self, event):
        message = event['message']
        await self.send_json({
                "type": event['type'],
                "message": message
            })