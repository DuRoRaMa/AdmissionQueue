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
        # await self.send_json(
        #     {
        #         'type': 'chat_message',
        #         'message': message
        #     }
        # )

    # Обработчик для события chat_message
    async def chat_message(self, event):
        message = event['message']
        # Отправка сообщения
        await self.send_json({ 'message': message })