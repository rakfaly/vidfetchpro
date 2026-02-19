from typing import Optional

from celery import shared_task
from celery.result import AsyncResult

from apps.downloads.services.video_metadata import VideoMetadataFetcher


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def run_fetch_metadata(self, url: str) -> dict:
    """Fetch video metadata inside a Celery worker."""
    # info = VideoMetadataFetcher().fetch(url, fast=True)
    # Return a trimmed payload to keep results small and fast.
    # return {
    #     "id": info.get("id"),
    #     "title": info.get("title"),
    #     "uploader": info.get("uploader"),
    #     "duration": info.get("duration"),
    #     "thumbnail": info.get("thumbnail"),
    #     "height": info.get("height"),
    #     "webpage_url": info.get("webpage_url") or info.get("original_url"),
    #     "upload_date": info.get("upload_date"),
    #     "formats": info.get("formats", []),
    #     "filesize": info.get("filesize"),
    #     "filesize_approx": info.get("filesize_approx"),
    #     "entries": info.get("entries", []),
    # }

    return VideoMetadataFetcher().fetch(url, fast=False)


def enqueue_fetch_data(url: str) -> Optional[AsyncResult]:
    """Enqueue a metadata fetch task for a URL."""

    return run_fetch_metadata.delay(url)
