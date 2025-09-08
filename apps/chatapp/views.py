from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Message
from .serializers import MessageSerializer

class SendMessageAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        receiver_id = request.data.get("receiver_id")
        text = request.data.get("text")
        file = request.FILES.get("file")

        msg = Message.objects.create(
            sender=request.user,
            receiver_id=receiver_id,
            text=text,
            file=file
        )
        serializer = MessageSerializer(msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationAPI(APIView):
    """see all messages between two users"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        messages = Message.objects.filter(
            sender__in=[request.user.id, user_id],
            receiver__in=[request.user.id, user_id]
        ).order_by("timestamp")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class MarkDeliveredAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message_ids = request.data.get("message_ids", [])
        updated = Message.objects.filter(
            id__in=message_ids,
            receiver=request.user,
            delivered=False
        ).update(delivered=True)
        return Response({"updated": updated, "status": "delivered"})


class MarkSeenAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message_ids = request.data.get("message_ids", [])
        updated = Message.objects.filter(
            id__in=message_ids,
            receiver=request.user,
            seen=False
        ).update(seen=True)
        return Response({"updated": updated, "status": "seen"})


from rest_framework import generics, permissions
from .models import Message
from .serializers import MessageSerializer

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        other_user_id = self.kwargs['user_id']
        return Message.objects.filter(
            sender__in=[self.request.user.id, other_user_id],
            receiver__in=[self.request.user.id, other_user_id]
        ).order_by('timestamp')
