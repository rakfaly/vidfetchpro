import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    """Profile extension for application-specific user limits and plan data."""

    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    plan_tier = models.CharField(max_length=10, choices=PLAN_CHOICES, default="free")
    daily_limit = models.PositiveIntegerField(default=5)
    max_resolution = models.PositiveIntegerField(default=720)
    is_unlimited = models.BooleanField(default=False)

    def __str__(self):
        """Return a readable identifier for admin displays."""

        return f"{self.user.username} - {self.plan_tier}"
