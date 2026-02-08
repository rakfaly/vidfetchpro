from typing import Optional
from celery import shared_task
from celery.result import AsyncResult
from apps.downloads.services.video_metadata import VideoMetadataFetcher


# Fetch Video Metadata
@shared_task(
    bind=True, autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def run_fetch_metadata(self, url: str) -> dict:
    return VideoMetadataFetcher().fetch(url)


def enqueue_fetch_data(url: str) -> Optional[AsyncResult]:
    return run_fetch_metadata.delay(url)
    
