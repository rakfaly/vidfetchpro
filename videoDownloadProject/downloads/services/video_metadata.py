import json
from typing import Any, Dict

from apps.downloads.services.exceptions import DownloadFailed
from apps.downloads.services.validators import validate_url


class VideoMetadataFetcher:
    """Service class to fetch video metadata using yt-dlp."""

    def fetch(self, url: str, *, fast: bool = False) -> Dict[str, Any]:
        """Fetch metadata for a URL without downloading the media."""

        url = validate_url(url)
        try:
            from yt_dlp import YoutubeDL
        except Exception as exc:  # pragma: no cover - runtime dependency
            raise DownloadFailed("yt-dlp is not installed") from exc

        ydl_opts = {
            "quiet": True,
            "skip_download": False,
            "noplaylist": False,
            "socket_timeout": 15,
            "retries": 3,
            # Prefer Android client to reduce JS challenge friction.
            # "extractor_args": {"youtube": {"player_client": ["android"]}},
            # Enable JS challenge solver via remote components.
            "remote_components": ["ejs:github"],
            "js_runtimes": {"deno": {}},
        }
        if fast:
            ydl_opts.update(
                {
                    "extract_flat": True,
                    "noplaylist": True,
                }
            )

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return info

        # Dummy implementation for testing without yt-dlp
        # with open("assets/single_video_sample.json") as f:
        # with open("assets/playlist_video_sample.json") as f:
        #     info = json.load(f)
        #     return info
