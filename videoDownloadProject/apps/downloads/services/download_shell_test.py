from django.conf import settings
from django.contrib.auth import get_user_model

from apps.downloads.models import DownloadJob
from apps.downloads.tasks.download_tasks import enqueue_download_job
from apps.downloads.tasks.fetch_metadata_tasks import enqueue_fetch_data
from apps.videos.models import VideoFormat, VideoSource


def run_shell_test() -> None:
    video_url = "https://www.youtube.com/shorts/hE_jWgregjM?feature=share"

    fetch_result = enqueue_fetch_data(video_url)
    if fetch_result is None:
        raise RuntimeError("Fetch task did not return a result")
    info = fetch_result.get(timeout=300)

    user_model = get_user_model()
    user = user_model.objects.first()
    if user is None:
        user = user_model.objects.create_user(username="shell-test-user", password="shell-test-pass")

    video = VideoSource.objects.create(
        canonical_url=video_url,
        provider=info.get("extractor_key") or info.get("extractor") or "unknown",
        provider_video_id=info.get("id") or "",
        title=info.get("title") or "Test Video",
        channel_name=info.get("uploader") or "",
        thumbnail_url=info.get("thumbnail") or "",
        duration_seconds=info.get("duration"),
        raw_metadata=info,
    )

    formats = info.get("formats") or []
    created_formats = []
    for fmt in formats[:25]:
        is_audio_only = fmt.get("vcodec") in (None, "none")
        quality_label = fmt.get("format_note") or (f"{fmt.get('height')}p" if fmt.get("height") else "")
        created_formats.append(
            VideoFormat.objects.create(
                video=video,
                format_id=str(fmt.get("format_id") or ""),
                container=fmt.get("ext") or "mp4",
                quality_label=quality_label,
                width=fmt.get("width"),
                height=fmt.get("height"),
                codec_video=fmt.get("vcodec") or "",
                codec_audio=fmt.get("acodec") or "",
                is_audio_only=is_audio_only,
                size_bytes=fmt.get("filesize") or fmt.get("filesize_approx"),
            )
        )

    if not created_formats:
        raise RuntimeError("No formats returned by yt-dlp")

    def format_rank(vf: VideoFormat) -> tuple:
        return (
            1 if vf.container == "mp4" else 0,
            0 if vf.is_audio_only else 1,
            vf.height or 0,
        )

    fmt = sorted(created_formats, key=format_rank, reverse=True)[0]
    job = DownloadJob.objects.create(user=user, video=video, format=fmt)

    result = enqueue_download_job(job.id, use_on_commit=False)
    print(f"Enqueued DownloadJob {job.id} (task_id={getattr(result, 'id', None)})")

    is_eager = bool(
        getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
        or getattr(settings, "task_always_eager", False)
    )
    if is_eager and result is not None:
        result.get()
        job.refresh_from_db()
        print(f"Completed DownloadJob {job.id} with status={job.status}")
