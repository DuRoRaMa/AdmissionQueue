import json

from channels.generic.websocket import AsyncWebsocketConsumer


class OperatorNotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"operator_notifications_{user.pk}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        user = self.scope["user"]

        if user.is_authenticated:
            await self.channel_layer.group_discard(
                f"operator_notifications_{user.pk}",
                self.channel_name,
            )

    async def operator_notification(self, event):
        await self.send(
            text_data=json.dumps(event["data"], ensure_ascii=False)
        )