import uuid

from django.db import models

from apps.common.models import TimeStampedModel
from apps.downloads.models import DownloadJob


class History(TimeStampedModel):
    """Stores the outcome of a completed download job."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(DownloadJob, on_delete=models.CASCADE, related_name='history')
    success = models.BooleanField(default=False)

    def __str__(self):
        """Return a readable status label for admin displays."""

        return f"{self.job_id} - {'Success' if self.success else 'Failed'}"
