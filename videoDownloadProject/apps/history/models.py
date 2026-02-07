import uuid
from django.db import models

from apps.downloads.models import DownloadJob
from apps.common.models import TimeStampedModel

# Create your models here.
class History(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(DownloadJob, on_delete=models.CASCADE, related_name='history')
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.job_id} - {'Success' if self.success else 'Failed'}"
