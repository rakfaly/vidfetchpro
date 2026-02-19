from typing import Any, Dict, List

from apps.downloads.models import DownloadJob
from apps.downloads.services.access import enforce_download_constraints
from apps.downloads.services.video_metadata import VideoMetadataFetcher
from apps.downloads.tasks.download_tasks import enqueue_download_job
from apps.videos.models import VideoFormat, VideoSource
from utils.utils import normalize_entry


def _truncate(value: Any, max_len: int) -> str:
    """
    Coerce a value to string and truncate to max_len.

    Returns an empty string for None values.
    """
    if value is None:
        return ""
    return str(value)[:max_len]


def _create_formats(
    video: VideoSource,
    formats: List[Dict[str, Any]],
    *,
    use_filtered: bool = True,
) -> List[VideoFormat]:
    """
    Build unsaved VideoFormat records from yt-dlp format dictionaries.

    If `use_filtered` is True, applies `_filtered_formats` before mapping.
    """
    filtered_resolution_formats = (
        _filtered_formats(formats) if use_filtered else list(formats)
    )

    created: List[VideoFormat] = []
    for fmt in filtered_resolution_formats:
        is_audio_only = fmt.get("vcodec") in (None, "none")
        quality_label = fmt.get("format_note") or (
            f"{fmt.get('height')}p" if fmt.get("height") else ""
        )
        created.append(
            VideoFormat(
                video=video,
                format_id=_truncate(fmt.get("format_id"), 128),
                container=_truncate(fmt.get("ext") or "mp4", 16),
                quality_label=_truncate(
                    quality_label, 32
                ),  # limit to 32 characters (Models)
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
    """
    Choose a preferred format (MP4 video with highest resolution).

    Ranking prefers MP4, non-audio-only, then highest height.
    """

    def rank(vf: VideoFormat) -> tuple:
        return (
            1 if vf.container == "mp4" else 0,
            0 if vf.is_audio_only else 1,
            vf.height or 0,
        )

    return sorted(formats, key=rank, reverse=True)[0]


def _filtered_formats(raw_formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter formats based on size, container, and resolution.

    Keeps MP4 formats >= 480p, and audio-only formats.
    De-duplicates by max filesize per height.
    """
    seen_ids: set[str] = set()
    videos: List[Dict[str, Any]] = []
    audios: List[Dict[str, Any]] = []

    for fmt in raw_formats:
        format_id = str(fmt.get("format_id") or "").strip()
        if not format_id or format_id in seen_ids:
            continue
        seen_ids.add(format_id)

        if fmt.get("ext") == "mhtml":
            continue
        if str(fmt.get("format_note") or "").lower().find("storyboard") >= 0:
            continue

        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")
        height = fmt.get("height")
        is_audio_only = vcodec in (None, "none", "images") and acodec not in (
            None,
            "none",
        )
        is_video = vcodec not in (None, "none", "images")

        if is_video:
            # Keep all practical video formats from 144p upward.
            if not isinstance(height, int) or height < 144:
                continue
            videos.append(fmt)
            continue

        if is_audio_only:
            audios.append(fmt)

    videos.sort(
        key=lambda f: (
            f.get("height") or 0,
            1 if f.get("acodec") not in (None, "none") else 0,
            1 if f.get("ext") == "mp4" else 0,
            f.get("tbr") or 0,
        ),
        reverse=True,
    )
    audios.sort(key=lambda f: f.get("abr") or 0, reverse=True)

    # Limit list size for UI usability while keeping quality choices.
    return videos[:60] + audios[:12]


def fetch_data(playlist_url: str) -> List[Dict[str, Any]]:
    """
    Fetch raw metadata for a playlist or single video URL.

    Returns the raw yt-dlp info dict.
    """
    return VideoMetadataFetcher().fetch(playlist_url)


def build_playlist_preview(
    info: dict,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Build preview data for UI without saving any models.

    Returns:
    - normalized entry list
    - filtered format list
    """
    entries = info.get("entries") or []
    if not entries:
        entries = [info]
    _formats = [format for entry in entries for format in entry.get("formats", [])]
    formats = _filtered_formats(_formats)
    return (normalize_entry(entries), formats)


def launch_playlist_downloads(user, info: dict, format_id: str) -> List[DownloadJob]:
    """
    Persist playlist entries and enqueue downloads for a selected format.

    Creates VideoSource + VideoFormat records, enforces user constraints,
    and enqueues a download job per entry.
    """

    entries = info.get("entries") or []
    if not entries:
        entries = [info]

    jobs: List[DownloadJob] = []
    for entry in entries:
        entry_url = (
            entry.get("webpage_url") or entry.get("url") or entry.get("original_url")
        )
        if not entry_url:
            continue

        video, _ = VideoSource.objects.get_or_create(
            canonical_url=entry_url,
            defaults={
                "provider": entry.get("extractor_key")
                or entry.get("extractor")
                or "unknown",
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
            available_ids = [
                str(f.get("format_id"))
                for f in entry_formats
                if f.get("format_id") is not None
            ]
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
