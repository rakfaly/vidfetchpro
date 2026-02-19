"""Download tasks package."""

# Ensure Celery autodiscovery registers tasks in this package.
from .download_tasks import enqueue_download_job, run_download_job  # noqa: F401
from .fetch_metadata_tasks import enqueue_fetch_data, run_fetch_metadata  # noqa: F401
