from typing import Any, Dict

from apps.downloads.services.exceptions import DownloadFailed
from apps.downloads.services.validators import validate_url


class VideoMetadataFetcher:
    """Service class to fetch video metadata using yt-dlp."""

    def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch metadata for a URL without downloading the media."""

        url = validate_url(url)
        try:
            from yt_dlp import YoutubeDL
        except Exception as exc:  # pragma: no cover - runtime dependency
            raise DownloadFailed("yt-dlp is not installed") from exc

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
