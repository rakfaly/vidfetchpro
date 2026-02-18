from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.downloads.models import DailyDownloadUsage, DownloadJob
from apps.downloads.services.access import enforce_download_constraints
from apps.downloads.services.exceptions import RateLimitExceeded
from apps.downloads.tasks.download_tasks import (
    enqueue_download_job,
    run_download_job,
)
from apps.history.models import History
from apps.videos.models import VideoFormat, VideoSource


class DownloadTaskTests(TestCase):
    """Tests for download task enqueueing behavior."""

    def setUp(self) -> None:
        """Create baseline user, video, format, and job fixtures."""

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="test-user", password="test-pass"
        )
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
        self.job = DownloadJob.objects.create(
            user=self.user, video=self.video, format=self.format
        )

    def test_enqueue_download_job_calls_delay_immediately_when_no_on_commit(
        self,
    ) -> None:
        """`use_on_commit=False` should dispatch via Celery delay now."""

        with patch(
            "apps.downloads.tasks.download_tasks.run_download_job.delay"
        ) as mock_delay:
            result = enqueue_download_job(self.job.id, use_on_commit=False)
        self.assertIsNotNone(result)
        mock_delay.assert_called_once_with(self.job.id)

    def test_enqueue_download_job_on_commit_dispatches_after_commit(self) -> None:
        """`use_on_commit=True` should register callback and dispatch after commit."""

        with patch(
            "apps.downloads.tasks.download_tasks.run_download_job.delay"
        ) as mock_delay:
            with self.captureOnCommitCallbacks(execute=True):
                result = enqueue_download_job(self.job.id, use_on_commit=True)
            self.assertIsNone(result)
        mock_delay.assert_called_once_with(self.job.id)

    def test_run_download_job_success_creates_success_history_row(self) -> None:
        """Task execution success should create one History entry with success=True."""

        with patch("apps.downloads.tasks.download_tasks.VideoDownload") as mock_service:
            run_download_job.run(str(self.job.id))

        mock_service.assert_called_once()
        mock_service.return_value.download.assert_called_once_with()
        self.assertEqual(History.objects.filter(job=self.job).count(), 1)
        self.assertTrue(History.objects.get(job=self.job).success)
        usage = DailyDownloadUsage.objects.get(user=self.user, day=timezone.localdate())
        self.assertEqual(usage.success_count, 1)

    def test_run_download_job_failure_creates_failed_history_row(self) -> None:
        """Task execution failure should still create History entry with success=False."""

        with patch("apps.downloads.tasks.download_tasks.VideoDownload") as mock_service:
            mock_service.return_value.download.side_effect = RuntimeError(
                "download failed"
            )
            with self.assertRaises(RuntimeError):
                run_download_job.run(str(self.job.id))

        self.assertEqual(History.objects.filter(job=self.job).count(), 1)
        self.assertFalse(History.objects.get(job=self.job).success)


class DownloadConstraintsTests(TestCase):
    """Tests for plan-based daily download constraints."""

    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="limit-user", password="test-pass"
        )
        self.video = VideoSource.objects.create(
            canonical_url="https://example.com/video-limit",
            provider="example",
            title="Rate Limit Video",
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
        self.profile = self.user.profile
        self.profile.daily_limit = 1
        self.profile.is_unlimited = False
        self.profile.max_resolution = 720
        self.profile.save(update_fields=["daily_limit", "is_unlimited", "max_resolution"])

    def test_rate_limit_blocks_when_usage_counter_reaches_daily_limit(self) -> None:
        DailyDownloadUsage.objects.create(
            user=self.user, day=timezone.localdate(), success_count=1
        )

        with self.assertRaises(RateLimitExceeded):
            enforce_download_constraints(self.user, self.format)


class FetchStatusPollingTests(TestCase):
    """Tests for HTMX polling behavior during retry and final failure states."""

    def setUp(self) -> None:
        self.url = reverse("apps.downloads:fetch_status")

    def _set_fetch_task_id(self, task_id: str) -> None:
        session = self.client.session
        session["fetch_task_id"] = task_id
        session.save()

    def test_fetch_status_keeps_spinner_while_task_is_retrying(self) -> None:
        self._set_fetch_task_id("retry-task-id")

        class RetryResult:
            def successful(self) -> bool:
                return False

            def failed(self) -> bool:
                return False

            def ready(self) -> bool:
                return False

        with patch("apps.downloads.views.AsyncResult", return_value=RetryResult()):
            response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fetch-spinner")
        self.assertContains(response, 'hx-trigger="every 2s"')
        self.assertEqual(self.client.session.get("fetch_task_id"), "retry-task-id")

    def test_fetch_status_stops_polling_on_final_failure(self) -> None:
        self._set_fetch_task_id("final-failure-task-id")

        class FailureResult:
            def successful(self) -> bool:
                return False

            def failed(self) -> bool:
                return True

            def ready(self) -> bool:
                return True

        with patch("apps.downloads.views.AsyncResult", return_value=FailureResult()):
            response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Failed to fetch metadata")
        self.assertNotContains(response, "fetch-spinner")
        self.assertIsNone(self.client.session.get("fetch_task_id"))

    def test_rate_limit_counts_in_flight_jobs(self) -> None:
        DownloadJob.objects.create(
            user=self.user, video=self.video, format=self.format, status="queued"
        )

        with self.assertRaises(RateLimitExceeded):
            enforce_download_constraints(self.user, self.format)
