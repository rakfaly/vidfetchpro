from __future__ import annotations

from typing import Optional

from celery import shared_task
from celery.result import AsyncResult
from django.db import transaction

from apps.downloads.models import DownloadJob
from apps.history.models import History
from apps.downloads.services.video_download import VideoDownload


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def run_download_job(self, job_id: str) -> None:
    """Execute a download job by id inside a Celery worker."""

    job = DownloadJob.objects.select_related("video", "format", "user").get(id=job_id)
    try:
        VideoDownload(job).download()
        success = True
    except Exception:
        success = False
        raise
    finally:
        job.refresh_from_db()
        History.objects.create(job=job, success=success)


def enqueue_download_job(job_id: str, *, use_on_commit: bool = True) -> Optional[AsyncResult]:
    """Enqueue the download task; optionally wait for the DB transaction to commit."""
    if use_on_commit:
        transaction.on_commit(lambda: run_download_job.delay(job_id))
        return None
    return run_download_job.delay(job_id)
