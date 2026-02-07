import uuid
from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel

# Create your models here.
class UserProfile(TimeStampedModel):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan_tier = models.CharField(max_length=10, choices=PLAN_CHOICES, default='free')
    daily_limit = models.PositiveIntegerField(default=5)
    max_resolution = models.PositiveIntegerField(default=720)
    is_unlimited = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user_id} - {self.plan_tier}"
        