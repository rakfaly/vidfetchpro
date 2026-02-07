from django.contrib.auth import get_user_model
from apps.videos.models import VideoSource, VideoFormat
from apps.downloads.models import DownloadJob
from apps.downloads.services.video_download import VideoDownload

User = get_user_model()
user = User.objects.first()

video = VideoSource.objects.create(
    #canonical_url="https://www.youtube.com/watch?v=9chgOfdBmv4&themeRefresh=1",
    canonical_url="https://www.youtube.com/shorts/hE_jWgregjM?feature=share",
    provider="youtube",
    title="Test Video",
)

fmt = VideoFormat.objects.create(
    video=video,
    container="mp4",
    quality_label="720p",
    width=1280,
    height=720,
    codec_video="h264",
    codec_audio="aac",
    is_audio_only=False,
)

job = DownloadJob.objects.create(
    user=user,
    video=video,
    format=fmt,
)

VideoDownload(job).download()
