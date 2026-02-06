from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    name = models.CharField(max_length=100)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({'Online' if self.is_online else 'Offline'})"

class PairingToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=6)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return self.expires_at >= timezone.now()

    def __str__(self):
        return f"{self.token} for {self.user.username}"
