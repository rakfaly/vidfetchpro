import uuid

from django.db import models

from apps.common.models import TimeStampedModel


class VideoSource(TimeStampedModel):
    """Represents a single video entry and its extracted metadata."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_url = models.URLField(max_length=200, unique=True)  # may be need more max_length
    #provider = models.CharField(max_length=50, choices=[('youtube', 'YouTube'), ('vimeo', 'Vimeo')])
    provider = models.CharField(max_length=50,)
    provider_video_id = models.CharField(max_length=128, blank=True)

    title = models.CharField(max_length=300, blank=True)
    channel_name = models.CharField(max_length=200, blank=True)
    thumbnail_url = models.URLField(max_length=200, blank=True)
    duration_seconds = models.PositiveIntegerField(blank=True, null=True)

    raw_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        """Return a readable label for admin and logs."""

        return self.title or self.canonical_url


class VideoFormat(TimeStampedModel):
    """Stores an individual downloadable format for a video source."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(VideoSource, on_delete=models.CASCADE, related_name="formats")
    format_id = models.CharField(max_length=128, blank=True)  # yt-dlp format id
    container = models.CharField(max_length=16)  # mp4, webm, mp3
    quality_label = models.CharField(max_length=32, blank=True)  # 1080p, 720p
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    codec_video = models.CharField(max_length=32, blank=True)
    codec_audio = models.CharField(max_length=32, blank=True)

    is_audio_only = models.BooleanField(default=False)
    is_premium_only = models.BooleanField(default=False)

    size_bytes = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        """Return a compact label for the format."""

        return f"{self.container} {self.quality_label}".strip()
