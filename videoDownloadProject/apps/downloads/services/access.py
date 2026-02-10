from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from apps.downloads.models import DownloadJob
from apps.downloads.services.validators import ensure_format_allowed, ensure_rate_limit


@dataclass(frozen=True)
class DownloadPolicy:
    """Simple policy holder for download limits and capabilities."""

    daily_limit: int | None
    max_resolution: int | None
    is_unlimited: bool = False


def enforce_download_constraints(user, video_format) -> None:
    """Apply rate-limit and format constraints before creating a job."""
    if user and getattr(user, "is_authenticated", False):
        profile = getattr(user, "profile", None)
        if profile is None:
            profile = DownloadPolicy(
                daily_limit=getattr(settings, "VIDEO_DEFAULT_DAILY_LIMIT", 5),
                max_resolution=getattr(settings, "VIDEO_DEFAULT_MAX_RESOLUTION", 720),
                is_unlimited=False,
            )
        downloads_today = DownloadJob.objects.filter(
            user=user, created_at__date=timezone.now().date()
        ).count()
    else:
        profile = DownloadPolicy(
            daily_limit=getattr(settings, "VIDEO_ANON_DAILY_LIMIT", 3),
            max_resolution=getattr(settings, "VIDEO_ANON_MAX_RESOLUTION", 480),
            is_unlimited=False,
        )
        downloads_today = 0

    ensure_rate_limit(profile, downloads_today)
    ensure_format_allowed(profile, video_format)
