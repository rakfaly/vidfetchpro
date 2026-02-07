from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from apps.downloads.services.exceptions import InvalidVideoUrl, RateLimitExceeded, FormatNotAllowed


def validate_url(value: str) -> str:
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
    if profile and profile.is_unlimited:
        return
    if profile and profile.daily_limit is not None and downloads_today >= profile.daily_limit:
        raise RateLimitExceeded("Daily download limit exceeded")


def ensure_format_allowed(profile, video_format) -> None:
    if profile and profile.is_unlimited:
        return

    if profile and profile.max_resolution and video_format.height:
        if video_format.height > profile.max_resolution:
            raise FormatNotAllowed("Selected format is not allowed for your plan")

    if video_format.is_premium_only:
        raise FormatNotAllowed("Selected format is premium only")
