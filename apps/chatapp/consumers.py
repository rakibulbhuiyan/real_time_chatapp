import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import *

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        self.other_user = await self.get_user(self.other_user_id)
        self.room_group_name = f"chat_{min(self.user.id, self.other_user.id)}_{max(self.user.id, self.other_user.id)}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        # new txt send
        if action == "send_message":
            message = data.get("message")
            file_url = data.get("file")

            msg_obj = await self.save_message(self.user, self.other_user, message, file_url)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "id": msg_obj.id,
                    "message": msg_obj.text,
                    "file": msg_obj.file.url if msg_obj.file else None,
                    "sender": self.user.username,
                    "timestamp": str(msg_obj.timestamp),
                    "status": "sent"
                }
            )
