class VideoDownloadError(Exception):
    """Base class for download errors."""


class InvalidVideoUrl(VideoDownloadError):
    """URL is missing or not supported."""


class RateLimitExceeded(VideoDownloadError):
    """User exceeded allowed download limits."""


class FormatNotAllowed(VideoDownloadError):
    """Selected format is not allowed for this user."""


class DownloadFailed(VideoDownloadError):
    """Download failed during processing."""
