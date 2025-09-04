from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from .serializers import NotificationSerializer

@shared_task
def send_push_notification(notification_id):
    notification = Notification.objects.get(id=notification_id)
    serializer = NotificationSerializer(notification)
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{notification.user.id}", # Ensure this matches the group name in the consumer
        {
            "type": "send_notification",
            "message": serializer.data
        }
    )