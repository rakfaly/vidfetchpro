from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.test.utils import capture_on_commit_callbacks

from apps.downloads.models import DownloadJob
from apps.downloads.tasks.download_tasks import enqueue_download_job
from apps.videos.models import VideoFormat, VideoSource


class DownloadTaskTests(TestCase):
    """Tests for download task enqueueing behavior."""

    def setUp(self) -> None:
        """Create baseline user, video, format, and job fixtures."""

        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="test-user", password="test-pass")
        self.video = VideoSource.objects.create(
            canonical_url="https://example.com/video",
            provider="example",
            title="Test Video",
        )
        self.format = VideoFormat.objects.create(
            video=self.video,
            container="mp4",
            quality_label="720p",
            width=1280,
            height=720,
            codec_video="h264",
            codec_audio="aac",
            is_audio_only=False,
        )
        self.job = DownloadJob.objects.create(user=self.user, video=self.video, format=self.format)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_enqueue_download_job_runs_task_immediately(self) -> None:
        """Ensure eager mode executes the task immediately."""

        with patch("apps.downloads.tasks.download_tasks.VideoDownload") as mock_service:
            result = enqueue_download_job(self.job.id, use_on_commit=False)
            self.assertIsNotNone(result)
            mock_service.assert_called_once()
            mock_service.return_value.download.assert_called_once_with()

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_enqueue_download_job_on_commit(self) -> None:
        """Ensure on-commit enqueue runs after callbacks are executed."""

        with patch("apps.downloads.tasks.download_tasks.VideoDownload") as mock_service:
            with capture_on_commit_callbacks(execute=True):
                result = enqueue_download_job(self.job.id, use_on_commit=True)
            self.assertIsNone(result)
            mock_service.assert_called_once()
