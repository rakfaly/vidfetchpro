from dataclasses import dataclass

from django.conf import settings
from django.db.models import F
from django.db import transaction
from django.utils import timezone

from apps.downloads.models import DailyDownloadUsage, DownloadJob
from apps.downloads.services.validators import ensure_format_allowed, ensure_rate_limit


@dataclass(frozen=True)
class DownloadPolicy:
    """Simple policy holder for download limits and capabilities."""

    daily_limit: int | None
    max_resolution: int | None
    is_unlimited: bool = False


def enforce_download_constraints(user, video_format) -> None:
    """Apply rate-limit and format constraints before creating a job."""
    today = timezone.localdate()

    if user and getattr(user, "is_authenticated", False):
        profile = getattr(user, "profile", None)
        if profile is None:
            profile = DownloadPolicy(
                daily_limit=getattr(settings, "VIDEO_DEFAULT_DAILY_LIMIT", 5),
                max_resolution=getattr(settings, "VIDEO_DEFAULT_MAX_RESOLUTION", 720),
                is_unlimited=False,
            )
            usage_count_today = (
                DailyDownloadUsage.objects.filter(user=user, day=today)
                .values_list("success_count", flat=True)
                .first()
                or 0
            )
            active_count_today = DownloadJob.objects.filter(
                user=user,
                created_at__date=today,
                status__in=("queued", "downloading"),
            ).count()
            downloads_today = usage_count_today + active_count_today
            ensure_rate_limit(profile, downloads_today)
            ensure_format_allowed(profile, video_format)
            return

        # Serialize quota checks per user to avoid concurrent over-enqueue.
        with transaction.atomic():
            type(profile).objects.select_for_update().get(pk=profile.pk)
            usage, _ = DailyDownloadUsage.objects.select_for_update().get_or_create(
                user=user,
                day=today,
                defaults={"success_count": 0},
            )
            active_count_today = DownloadJob.objects.filter(
                user=user,
                created_at__date=today,
                status__in=("queued", "downloading"),
            ).count()
            downloads_today = usage.success_count + active_count_today
            ensure_rate_limit(profile, downloads_today)
            ensure_format_allowed(profile, video_format)
        return

    profile = DownloadPolicy(
        daily_limit=getattr(settings, "VIDEO_ANON_DAILY_LIMIT", 3),
        max_resolution=getattr(settings, "VIDEO_ANON_MAX_RESOLUTION", 480),
        is_unlimited=False,
    )
    ensure_rate_limit(profile, 0)
    ensure_format_allowed(profile, video_format)


def increment_daily_success_usage(user) -> None:
    """Increment successful daily usage counter for an authenticated user."""
    if not user or not getattr(user, "is_authenticated", False):
        return

    today = timezone.localdate()
    with transaction.atomic():
        usage, _ = DailyDownloadUsage.objects.select_for_update().get_or_create(
            user=user, day=today, defaults={"success_count": 0}
        )
        type(usage).objects.filter(pk=usage.pk).update(
            success_count=F("success_count") + 1
        )
