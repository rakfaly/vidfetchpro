from typing import Any, Dict, Iterable, List

from apps.downloads.models import DownloadJob
from apps.downloads.services.access import enforce_download_constraints
from apps.downloads.services.video_metadata import VideoMetadataFetcher
from apps.downloads.tasks.download_tasks import enqueue_download_job
#from apps.downloads.tasks.fetch_metadata_tasks import enqueue_fetch_data 
from apps.videos.models import VideoFormat, VideoSource


def _create_formats(video: VideoSource, formats: Iterable[Dict[str, Any]]) -> List[VideoFormat]:
    """Create VideoFormat records from yt-dlp format dictionaries."""
    filtered_resolution_formats = _filtered_formats(formats) or formats
    
    created: List[VideoFormat] = []
    for fmt in filtered_resolution_formats:
        is_audio_only = fmt.get("vcodec") in (None, "none")
        quality_label = fmt.get("format_note") or (f"{fmt.get('height')}p" if fmt.get("height") else "")
        created.append(
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
    return created


def _choose_format(formats: List[VideoFormat]) -> VideoFormat:
    """Choose a preferred format (MP4 video with highest resolution)."""
    def rank(vf: VideoFormat) -> tuple:
        return (
            1 if vf.container == "mp4" else 0,
            0 if vf.is_audio_only else 1,
            vf.height or 0,
        )
    return sorted(formats, key=rank, reverse=True)[0]


def _filtered_formats(raw_formats):
    """Filter formats based on size and resolution."""
    formats = []
    for format in raw_formats:
        if (format.get("filesize") is not None) and (format.get("filesize") >= 5000):
            if (format.get("width") is not None) and (format.get("width") >= 480):
                formats.append(format)
            elif format.get("vcodec") in (None, "none"): # audio aonly formats
                formats.append(format)
            else:
                pass
    return formats
    
    
def fetch_data(playlist_url):
    return VideoMetadataFetcher().fetch(playlist_url)
    

def enqueue_playlist_downloads(user, playlist_url: str) -> List[DownloadJob]:
    """Enqueue downloads for each playlist entry and return created jobs."""
    info = fetch_data(playlist_url)
    #entry_info = enqueue_fetch_data(entry_url) # in view mode when user click on fetch button
    entries = info.get("entries") or []
    if not entries:
        entries = [info]

    jobs: List[DownloadJob] = []
    for entry in entries:
        entry_url = entry.get("webpage_url") or entry.get("url")
        if not entry_url:
            continue

        video, _ = VideoSource.objects.get_or_create(
            canonical_url=entry_url,
            defaults={
                "provider": entry.get("extractor_key") or entry.get("extractor") or "unknown",
                "provider_video_id": entry.get("id") or "",
                "title": entry.get("title") or "Untitled",
                "channel_name": entry.get("uploader") or "",
                "thumbnail_url": entry.get("thumbnail") or "",
                "duration_seconds": entry.get("duration"),
                "raw_metadata": entry,
            },
        )

        formats = entry.get("formats") or []
        if not formats:
            entry_info = VideoMetadataFetcher().fetch(entry_url)
            # entry_info = enqueue_fetch_data(entry_url) # in view mode when user click on fetch button
            formats = entry_info.get("formats") or []
        
        created_formats = _create_formats(video, formats)
        if not created_formats:
            continue

        chosen_format = _choose_format(created_formats)
        enforce_download_constraints(user, chosen_format)

        job = DownloadJob.objects.create(user=user, video=video, format=chosen_format)
        enqueue_download_job(job.id, use_on_commit=False)
        jobs.append(job)

    return jobs
