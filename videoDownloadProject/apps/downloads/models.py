# apps/downloads/models.py
import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel
from apps.videos.models import VideoSource, VideoFormat


class DownloadJob(TimeStampedModel):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("downloading", "Downloading"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="downloads")
    video = models.ForeignKey(VideoSource, on_delete=models.PROTECT, related_name="downloads")
    format = models.ForeignKey(VideoFormat, on_delete=models.PROTECT, related_name="downloads")

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="queued")
    progress_percent = models.PositiveSmallIntegerField(default=0)
    bytes_downloaded = models.BigIntegerField(default=0)
    bytes_total = models.BigIntegerField(null=True, blank=True)
    speed_kbps = models.PositiveIntegerField(null=True, blank=True)
    eta_seconds = models.PositiveIntegerField(null=True, blank=True)

    output_filename = models.CharField(max_length=255, blank=True)
    failure_reason = models.TextField(blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        #return f"{self.user_id} - {self.status}"
        return f"{self.user} - {self.status}"
