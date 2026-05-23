# devices/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


# Stores paired camera devices
class Device(models.Model):

    # Device owner
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="devices"
    )

    # Camera name
    name = models.CharField(max_length=100)

    # Online/offline status
    is_online = models.BooleanField(default=False)

    # Last heartbeat time
    last_seen = models.DateTimeField(
        null=True,
        blank=True
    )

    # Device creation time
    created_at = models.DateTimeField(auto_now_add=True)

    # Permanent unique secret for reconnect/authentication
    secret_key = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    def __str__(self):
        return self.name


# Temporary token used during first-time pairing
class PairingToken(models.Model):

    # User who created token
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # Pairing code
    token = models.CharField(
        max_length=6,
        unique=True
    )

    # Token expiry time
    expires_at = models.DateTimeField()

    # Prevent token reuse
    used = models.BooleanField(default=False)

    # Check token validity
    def is_valid(self):
        return (
            not self.used and
            self.expires_at >= timezone.now()
        )

    def __str__(self):
        return self.token