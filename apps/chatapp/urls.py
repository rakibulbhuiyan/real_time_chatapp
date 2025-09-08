from django.urls import path
from .views import SendMessageAPI, ConversationAPI, MarkDeliveredAPI, MarkSeenAPI

urlpatterns = [
    path("send/", SendMessageAPI.as_view(), name="send_message"),
    path("conversation/<int:user_id>/", ConversationAPI.as_view(), name="conversation"),
    path("delivered/", MarkDeliveredAPI.as_view(), name="mark_delivered"),
    path("seen/", MarkSeenAPI.as_view(), name="mark_seen"),
]
