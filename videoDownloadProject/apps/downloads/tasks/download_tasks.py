from django.db import transaction
from django.tasks import task

from apps.downloads.models import DownloadJob
from apps.downloads.services.video_download import VideoDownload


@task
def run_download_job(job_id: str) -> None:
    job = DownloadJob.objects.select_related("video", "format", "user").get(id=job_id)
    VideoDownload(job).download()


def enqueue_download_job(job_id: str) -> None:
    """Enqueue the download task after the current transaction commits."""
    transaction.on_commit(lambda: run_download_job.enqueue(job_id=job_id))
