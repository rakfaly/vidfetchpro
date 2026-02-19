import json
from typing import Any, Dict

from apps.downloads.services.exceptions import DownloadFailed
from apps.downloads.services.validators import validate_url
from apps.downloads.services.yt_auth import build_ytdlp_common_opts, cookies_enabled, is_auth_challenge_error


class VideoMetadataFetcher:
    """Service class to fetch video metadata using yt-dlp."""

    @staticmethod
    def _has_video_formats(info: Dict[str, Any]) -> bool:
        entries = info.get("entries") or [info]
        for entry in entries:
            for fmt in entry.get("formats", []) or []:
                if fmt.get("vcodec") not in (None, "none", "images"):
                    return True
        return False

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
        }
        ydl_opts.update(build_ytdlp_common_opts())
        if fast:
            ydl_opts.update(
                {
                    "extract_flat": True,
                    "noplaylist": True,
                }
            )

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # Some YouTube client profiles intermittently return audio-only sets.
                # Retry with broader/default client options to recover video formats.
                if "youtube.com" in url and not self._has_video_formats(info):
                    try:
                        fallback_opts = dict(ydl_opts)
                        fallback_opts.pop("extractor_args", None)
                        with YoutubeDL(fallback_opts) as fallback_ydl:
                            fallback_info = fallback_ydl.extract_info(url, download=False)
                            if self._has_video_formats(fallback_info):
                                return fallback_info
                    except Exception:
                        # Keep primary result instead of failing entire metadata fetch.
                        pass
                return info
        except Exception as exc:
            message = str(exc)
            if is_auth_challenge_error(message):
                if not cookies_enabled():
                    raise DownloadFailed(
                        "YouTube requires valid authenticated cookies on the worker server. "
                        "Set YTDLP_COOKIES_B64 (or YTDLP_COOKIES_FILE) on both web and worker services."
                    ) from exc
                raise DownloadFailed(
                    "YouTube rejected current cookies. Re-export fresh YouTube cookies and update YTDLP_COOKIES_B64."
                ) from exc
            raise

        # Dummy implementation for testing without yt-dlp
        # with open("assets/single_video_sample.json") as f:
        # with open("assets/playlist_video_sample.json") as f:
        #     info = json.load(f)
        #     return info
