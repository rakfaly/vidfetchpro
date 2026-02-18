import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    """Profile extension for application-specific user limits and plan data."""

    PLAN_FREE = "free"
    PLAN_PRO = "pro"
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PRO, "Pro"),
    ]
    PLAN_POLICIES = {
        PLAN_FREE: {"daily_limit": 5, "max_resolution": 720, "is_unlimited": False},
        PLAN_PRO: {"daily_limit": 1000, "max_resolution": 4320, "is_unlimited": True},
    }
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    plan_tier = models.CharField(max_length=10, choices=PLAN_CHOICES, default=PLAN_FREE)
    daily_limit = models.PositiveIntegerField(default=5)
    max_resolution = models.PositiveIntegerField(default=720)
    is_unlimited = models.BooleanField(default=False)

    def __str__(self):
        """Return a readable identifier for admin displays."""

        return f"{self.user.username} - {self.plan_tier}"

    def apply_plan(self, plan_tier: str) -> None:
        """Apply a plan tier and synchronize profile limits."""
        resolved_tier = plan_tier if plan_tier in self.PLAN_POLICIES else self.PLAN_FREE
        policy = self.PLAN_POLICIES[resolved_tier]
        self.plan_tier = resolved_tier
        self.daily_limit = policy["daily_limit"]
        self.max_resolution = policy["max_resolution"]
        self.is_unlimited = policy["is_unlimited"]
