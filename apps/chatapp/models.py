from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
User = get_user_model()


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    delivered = models.BooleanField(default=False)  #  message reached receiver
    seen = models.BooleanField(default=False)       #  message read by receiver

    class Meta:
        ordering = ['timestamp']    
    
    def __str__(self):
        return f'Message from {self.sender} to {self.receiver} at {self.timestamp}'

