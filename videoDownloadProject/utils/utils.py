import math
import re
from datetime import datetime


def format_duration(seconds: float | int) -> str:
    if not isinstance(seconds, (int, float)) or math.isnan(seconds) or math.isinf(seconds) or seconds < 0:
        return ""
    total = int(seconds)
    hrs = total // 3600
    mins = (total % 3600) // 60
    secs = total % 60
    if hrs > 0:
        return f"{hrs}:{mins:02d}:{secs:02d}s"
    return f"{mins}:{secs:02d}s" 


def format_bytes(bytes_value: float | int) -> str:
    if not isinstance(bytes_value, (int, float)) or math.isnan(bytes_value) or math.isinf(bytes_value) or bytes_value < 0:
        return ""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(bytes_value)
    i = 0
    while value >= 1024 and i < len(units) - 1:
        value /= 1024
        i += 1
    decimals = 1 if value < 10 and i > 0 else 0
    return f"{value:.{decimals}f} {units[i]}"


def format_date(value: str | None) -> str:
    if not isinstance(value, str) or not re.match(r"^\d{8}$", value):
        return ""
    try:
        date = datetime.strptime(value, "%Y%m%d")
        return date.strftime("%B %d, %Y")  # e.g., "February 13, 2026"
    except ValueError:
        return ""


def normalize_entry(entries: list[dict]) -> list[dict]:
    data = map(lambda entry: {
        "id": entry.get("id"),
        "title": entry.get("title"),
        "thumbnail": entry.get("thumbnail"),
        "height": entry.get("height"),
        "uploader": entry.get("uploader"),
        "extractor": entry.get("extractor"),
        "duration": format_duration(entry.get("duration")),
        "filesize": format_bytes(entry.get("filesize")) or format_bytes(entry.get("filesize_approx")),
        "upload_date": format_date(entry.get("upload_date")),
        "formats": entry.get("formats"),
        "entries": entry.get("entries", []),
    }, entries)
    return list(data)


def unique_by_key_max(items: list[dict], key: str, max_by: str) -> list[dict]:
    """Keep item with highest max_by value for each unique key."""
    result = {}
    for d in items:
        k = d[key]
        if k not in result or d[max_by] > result[k][max_by]:
            result[k] = d
    return list(result.values())


def convert_bandwidth_binary(speed_kbps):
    """
    Convert bandwidth using binary units (1024-based)
    """
    if speed_kbps >= 1048576:  # 1024^2
        return f"{speed_kbps / 1048576:.2f} Gb/s"
    elif speed_kbps >= 1024:
        return f"{speed_kbps / 1024:.2f} Mb/s"
    else:
        return f"{speed_kbps:.2f} kb/s"
