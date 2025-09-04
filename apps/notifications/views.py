from requests import Response
from rest_framework import generics
from .models import Notification, Post
from .serializers import NotificationSerializer
from .tasks import send_push_notification

class NotificationCreateAPIView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post_id")
        comment = request.data.get('comment')

        post = Post.objects.get(id = post_id)

        # create notifications
        notification = Notification.objects.create(
            user = post.user,
            message = f"{request.user.username} commented : {comment}"
        )

        # celery async push notification
        send_push_notification.delay(notification.id)
        return Response({"success":True, "message" : "Comment added & notification sent!"})

