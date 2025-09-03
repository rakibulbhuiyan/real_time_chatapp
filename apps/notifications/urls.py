from django.urls import path
from .views import NotificationCreateAPIView

urlpatterns = [
    path("create/", NotificationCreateAPIView.as_view(), name="create-notification"),
]
