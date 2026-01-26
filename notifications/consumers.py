from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print("Websocket connected")
            print("Joined group:", self.group_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Websocket disconnected")

    async def send_notification(self, event):
        sender_role = event.get("sender_role", "Admin")
        user_notifications = await database_sync_to_async(lambda: Notification.objects.filter(receiver=self.user, is_read=False).count())()
        await self.send(text_data=json.dumps({
            "source": sender_role.capitalize(),
            "title": event["title"],
            "message": event["message"],
            "unread_count": user_notifications
        }))


# import json

# from channels.generic.websocket import AsyncWebsocketConsumer


# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = f"chat_{self.room_name}"

#         # Join room group
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]

#         # Send message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name, {"type": "chat.message", "message": message}
#         )

#     # Receive message from room group
#     async def chat_message(self, event):
#         message = event["message"]

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({"message": message}))
