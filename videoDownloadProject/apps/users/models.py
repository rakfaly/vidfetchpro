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
    SUBSCRIPTION_INACTIVE = "inactive"
    SUBSCRIPTION_PENDING = "pending"
    SUBSCRIPTION_ACTIVE = "active"
    SUBSCRIPTION_PAST_DUE = "past_due"
    SUBSCRIPTION_CANCELING = "canceling"
    SUBSCRIPTION_CANCELED = "canceled"
    SUBSCRIPTION_STATE_CHOICES = [
        (SUBSCRIPTION_INACTIVE, "Inactive"),
        (SUBSCRIPTION_PENDING, "Pending"),
        (SUBSCRIPTION_ACTIVE, "Active"),
        (SUBSCRIPTION_PAST_DUE, "Past Due"),
        (SUBSCRIPTION_CANCELING, "Canceling"),
        (SUBSCRIPTION_CANCELED, "Canceled"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    plan_tier = models.CharField(max_length=10, choices=PLAN_CHOICES, default=PLAN_FREE)
    daily_limit = models.PositiveIntegerField(default=5)
    max_resolution = models.PositiveIntegerField(default=720)
    is_unlimited = models.BooleanField(default=False)
    subscription_state = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATE_CHOICES,
        default=SUBSCRIPTION_INACTIVE,
    )
    provider_customer_id = models.CharField(max_length=128, blank=True, default="")
    provider_subscription_id = models.CharField(max_length=128, blank=True, default="")
    last_subscription_event_id = models.CharField(max_length=128, blank=True, default="")
    current_period_end = models.DateTimeField(null=True, blank=True)

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
        if resolved_tier == self.PLAN_PRO:
            self.subscription_state = self.SUBSCRIPTION_ACTIVE
        else:
            self.subscription_state = self.SUBSCRIPTION_INACTIVE


class SubscriptionEvent(TimeStampedModel):
    """Stores provider subscription events for idempotent processing/audits."""

    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=64)
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_events",
    )
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"{self.event_type} ({self.event_id})"
