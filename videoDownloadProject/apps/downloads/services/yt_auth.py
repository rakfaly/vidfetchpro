import base64
import os
from pathlib import Path
from typing import Any

from django.conf import settings

_COOKIE_CACHE_PATH = Path("/tmp/yt_cookies.txt")


def _materialize_cookie_file_from_env() -> str:
    raw = os.environ.get("YTDLP_COOKIES_B64", "").strip()
    if not raw:
        return ""
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
    except Exception:
        return ""

    _COOKIE_CACHE_PATH.write_text(decoded, encoding="utf-8")
    return str(_COOKIE_CACHE_PATH)


def build_ytdlp_common_opts() -> dict[str, Any]:
    opts: dict[str, Any] = {
        # Android client generally triggers fewer JS/bot challenges.
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "remote_components": ["ejs:github"],
    }

    cookiefile = (getattr(settings, "YTDLP_COOKIES_FILE", "") or "").strip()
    if not cookiefile:
        cookiefile = _materialize_cookie_file_from_env()
    if cookiefile:
        opts["cookiefile"] = cookiefile

    return opts


def is_auth_challenge_error(message: str) -> bool:
    text = (message or "").lower()
    return "sign in to confirm you're not a bot" in text or "cookies" in text
