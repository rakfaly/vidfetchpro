from typing import Any, Dict, Iterable, List

from apps.downloads.models import DownloadJob
from apps.downloads.services.access import enforce_download_constraints
from apps.downloads.services.video_metadata import VideoMetadataFetcher
from apps.downloads.tasks.download_tasks import enqueue_download_job
from apps.videos.models import VideoFormat, VideoSource
from utils.utils import normalize_entry, unique_by_key_max

def _truncate(value: Any, max_len: int) -> str:
    """Coerce a value to string and truncate to max_len."""
    if value is None:
        return ""
    return str(value)[:max_len]


def _create_formats(
    video: VideoSource,
    formats: Iterable[Dict[str, Any]],
    *,
    use_filtered: bool = True,
) -> List[VideoFormat]:
    """Create VideoFormat records from yt-dlp format dictionaries."""
    filtered_resolution_formats = _filtered_formats(formats) if use_filtered else list(formats)
    
    created: List[VideoFormat] = []
    for fmt in filtered_resolution_formats:
        is_audio_only = fmt.get("vcodec") in (None, "none")
        quality_label = fmt.get("format_note") or (f"{fmt.get('height')}p" if fmt.get("height") else "")
        created.append(
            VideoFormat(
                video=video,
                format_id=_truncate(fmt.get("format_id"), 128),
                container=_truncate(fmt.get("ext") or "mp4", 16),
                quality_label=_truncate(quality_label, 32),     # limit to 32 characters (Models)
                width=fmt.get("width"),
                height=fmt.get("height"),
                codec_video=_truncate(fmt.get("vcodec"), 32),
                codec_audio=_truncate(fmt.get("acodec"), 32),
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


def _filtered_formats(raw_formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter formats based on size and resolution."""
    formats = []
    for format in raw_formats:
        if (format.get("filesize") is not None) and (format.get("filesize") >= 5000) and (format.get("ext") in ("mp4")):
            if (format.get("height") is not None) and (format.get("height") >= 480):
                formats.append(format)
            elif format.get("vcodec") in (None, "none"): # audio aonly formats
                formats.append(format)
            else:
                pass
    formats = unique_by_key_max(formats, key="height", max_by="filesize")
    return sorted(formats, key=lambda f: f.get("height") or 0, reverse=True)

    
def fetch_data(playlist_url: str) -> Dict[str, Any]:
    """Fetch raw metadata for a playlist or single video URL."""
    return VideoMetadataFetcher().fetch(playlist_url)
    

def build_playlist_preview(info: dict) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build preview data for UI without saving any models."""
    entries = info.get("entries") or []
    if not entries:
        entries = [info]
    _formats = [format for entry in entries for format in entry.get("formats", [])]
    formats = _filtered_formats(_formats)
    return (normalize_entry(entries), formats)


def launch_playlist_downloads(user, info: dict, format_id: str) -> List[DownloadJob]:
    """Persist playlist entries and enqueue downloads."""

    entries = info.get("entries") or []
    if not entries:
        entries = [info]

    jobs: List[DownloadJob] = []
    for entry in entries:
        entry_url = entry.get("webpage_url") or entry.get("url") or entry.get("original_url")
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

        entry_formats = entry.get("formats") or []
        if not entry_formats:
            entry_info = VideoMetadataFetcher().fetch(entry_url)
            entry_formats = entry_info.get("formats") or []

        selected_formats = [
            f for f in entry_formats if str(f.get("format_id")) == str(format_id)
        ]
        if not selected_formats:
            available_ids = [str(f.get("format_id")) for f in entry_formats if f.get("format_id") is not None]
            print("No matching format_id:", format_id, "available:", available_ids[:20])
            continue

        created_formats = _create_formats(video, selected_formats, use_filtered=False)
        if not created_formats:
            continue

        chosen_format = created_formats[0]
        enforce_download_constraints(user, chosen_format)

        chosen_format.save()
        job = DownloadJob.objects.create(user=user, video=video, format=chosen_format)
        enqueue_download_job(job.id, use_on_commit=False)
        jobs.append(job)

    return jobs
