from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer
from .tasks import send_push_notification

class NotificationCreateAPIView(generics.CreateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def perform_create(self, serializer):
        notification = serializer.save()
        send_push_notification.delay(notification.id)  # Trigger Celery task