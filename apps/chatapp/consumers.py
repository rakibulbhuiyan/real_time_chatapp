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
             # 👁️ Seen status update
        elif action == "message_seen":
            message_ids = data.get("message_ids", [])
            await self.mark_messages_as_seen(message_ids, self, other_user=self.other_user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "messages_seen",
                    "message_ids": message_ids,
                    "seen_by": self.user.username,
                    "status": "seen"
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "message": event["message"],
            "file": event["file"],
            "sender": event["sender"],
            "timestamp": event["timestamp"],
            "status": event["status"]
        }))
        await self.mark_messages_as_delivered([event["id"]], self.other_user)
        
    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            "message_ids": event["message_ids"],
            "status": event["status"],
            "updated_by": event["updated_by"]
        }))
        await self.mark_messages_as_seen(event["message_ids"], self.other_user)


# ----------------- DB Operations -----------------
    @database_sync_to_async
    def save_message(self, sender, receiver, text, file_url=None):
        return Message.objects.create(sender=sender, receiver=receiver, text=text)
    
    @database_sync_to_async
    def mark_messages_as_delivered(self, message_ids, other_user):
        msg = Message.objects.filter(id__in=message_ids, receiver=other_user, status='sent')
        msg.delivered = True
        msg.save()
        return msg
    
    @database_sync_to_async
    def mark_messages_as_seen(self, message_ids, other_user):
        msg = Message.objects.filter(id__in=message_ids, receiver=other_user, status__in=['sent', 'delivered'])
        msg.update(seen=True, status='seen')
        return msg
    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)