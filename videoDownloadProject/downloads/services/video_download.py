import os
import time
from typing import Any, Dict

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.downloads.models import DownloadJob
from apps.downloads.services.exceptions import DownloadFailed
from apps.downloads.services.validators import ensure_format_allowed, validate_url


class VideoDownload:
    """Service class to download a video using yt-dlp."""

    def __init__(self, job: DownloadJob):
        """Initialize the service with a persisted download job."""

        self.job = job
        self.user = job.user
        self.video = job.video
        self.video_format = job.format

    def _build_output_dir(self) -> str:
        """Ensure the download output directory exists and return it."""

        base_dir = getattr(
            settings, "VIDEO_DOWNLOAD_ROOT", None
        )  # or os.path.join(settings.MEDIA_ROOT, "downloads")
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    def _build_output_filename(self) -> str:
        """Build a safe, readable output filename template."""

        base_title = self.video.title or "video"
        slug = slugify(base_title) or "video"
        slug = slug[:80]
        # return f"{slug}-{self.video.id}-{int(time.time())}.%(ext)s"
        return f"{slug}-{int(time.time())}.%(ext)s"

    def _progress_hook(self, data: Dict[str, Any]) -> None:
        """Persist progress updates emitted by yt-dlp."""

        if data.get("status") == "downloading":
            downloaded = data.get("downloaded_bytes") or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            speed = data.get("speed")
            eta = data.get("eta")

            percent = 0
            if total:
                percent = int(min(100, (downloaded / total) * 100))

            self.job.progress_percent = percent
            self.job.bytes_downloaded = downloaded
            self.job.bytes_total = total
            self.job.speed_kbps = int(speed / 1024) if speed else None
            self.job.eta_seconds = int(eta) if eta is not None else None
            self.job.status = "downloading"
            self.job.started_at = self.job.started_at or timezone.now()
            self.job.save(
                update_fields=[
                    "progress_percent",
                    "bytes_downloaded",
                    "bytes_total",
                    "speed_kbps",
                    "eta_seconds",
                    "status",
                    "started_at",
                    "updated_at",
                ]
            )

        if data.get("status") == "finished":
            self.job.progress_percent = 100
            self.job.status = "completed"
            self.job.completed_at = timezone.now()
            self.job.save(
                update_fields=[
                    "progress_percent",
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )

    def download(self) -> None:
        """Run the download and persist final metadata to the job."""
        ensure_format_allowed(getattr(self.user, "profile", None), self.video_format)

        url = validate_url(self.video.canonical_url)
        output_dir = self._build_output_dir()
        filename = self._build_output_filename()
        output_path = os.path.join(output_dir, filename)

        try:
            from yt_dlp import YoutubeDL
        except Exception as exc:  # pragma: no cover - runtime dependency
            raise DownloadFailed("yt-dlp is not installed") from exc

        # Prefer the exact format chosen by the user when available.
        if self.video_format.format_id:
            format_selector = self.video_format.format_id
            # Merge audio if the selected format is video-only.
            if self.video_format.codec_audio in ("", "none"):
                format_selector = f"{format_selector}+bestaudio/best"
        elif self.video_format.is_audio_only:
            format_selector = "bestaudio/best"
        else:
            # Enforce a minimum video height of 480p for video downloads.
            format_selector = (
                "bestvideo[height>=480][vcodec^=avc1]+bestaudio/best"
                "/bestvideo[height>=480]+bestaudio/best"
            )

        ydl_opts = {
            "format": format_selector,
            "outtmpl": output_path,
            "progress_hooks": [self._progress_hook],
            "noplaylist": True,
            "socket_timeout": 15,
            "retries": 3,
            "fragment_retries": 3,
            "concurrent_fragment_downloads": 8,
            # Prefer Android client to reduce JS challenge friction.
            "extractor_args": {"youtube": {"player_client": ["android"]}},
            # Enable JS challenge solver via remote components.
            "remote_components": ["ejs:github"],
            "js_runtimes": {"deno": {}},
            "cookiefile": settings.YTDLP_COOKIE_FILE,
        }

        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)

        with transaction.atomic():
            self.job.output_filename = os.path.basename(ydl.prepare_filename(result))
            self.job.status = "completed"
            self.job.completed_at = timezone.now()
            self.job.save(
                update_fields=[
                    "output_filename",
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )
