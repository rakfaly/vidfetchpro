from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from apps.downloads.services.exceptions import (
    FormatNotAllowed,
    InvalidVideoUrl,
    RateLimitExceeded,
)


def validate_url(value: str) -> str:
    """Validate a video URL and return the normalized string."""

    if not value:
        raise InvalidVideoUrl("URL is required")

    validator = URLValidator()
    try:
        validator(value)
    except ValidationError as exc:
        raise InvalidVideoUrl("Invalid video URL") from exc

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise InvalidVideoUrl("Invalid video URL")

    allowed_hosts = getattr(settings, "VIDEO_ALLOWED_HOSTS", None)
    if allowed_hosts and parsed.hostname not in allowed_hosts:
        raise InvalidVideoUrl("This provider is not allowed")

    return value


def ensure_rate_limit(profile, downloads_today: int) -> None:
    """Raise if the profile has exceeded its daily download limit."""

    if profile and profile.is_unlimited:
        return
    if (
        profile
        and (profile.daily_limit is not None)
        and downloads_today >= profile.daily_limit
    ):
        raise RateLimitExceeded("Daily download limit exceeded")


def ensure_format_allowed(profile, video_format) -> None:
    """Raise if the selected format violates plan restrictions."""

    if profile and profile.is_unlimited:
        return

    # `video_format` can be a Django model instance (VideoFormat) or a dict-like payload.
    height = (
        video_format.get("height")
        if isinstance(video_format, dict)
        else getattr(video_format, "height", None)
    )
    is_premium_only = (
        video_format.get("is_premium_only", False)
        if isinstance(video_format, dict)
        else getattr(video_format, "is_premium_only", False)
    )

    if profile and profile.max_resolution and height:
        if height > profile.max_resolution:
            raise FormatNotAllowed("Selected format is not allowed for your plan")

    if is_premium_only:
        raise FormatNotAllowed("Selected format is premium only")
