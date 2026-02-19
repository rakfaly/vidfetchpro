import base64
import logging
import os
from pathlib import Path
from typing import Any

from django.conf import settings

_COOKIE_CACHE_PATH = Path("/tmp/yt_cookies.txt")
logger = logging.getLogger(__name__)


def _clean_env(value: str) -> str:
    value = (value or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def _materialize_cookie_file_from_env() -> str:
    raw_b64 = _clean_env(os.environ.get("YTDLP_COOKIES_B64", ""))
    raw_text = _clean_env(os.environ.get("YTDLP_COOKIES_RAW", ""))

    if not raw_b64 and not raw_text:
        return str(_COOKIE_CACHE_PATH) if _COOKIE_CACHE_PATH.exists() else ""

    decoded = raw_text
    if raw_b64:
        try:
            decoded = base64.b64decode(raw_b64).decode("utf-8")
        except Exception:
            logger.warning("Invalid YTDLP_COOKIES_B64; unable to decode")
            return ""

    if "youtube.com" not in decoded and ".youtube.com" not in decoded:
        logger.warning("Decoded cookies do not appear to contain youtube.com entries")
        return ""

    _COOKIE_CACHE_PATH.write_text(decoded, encoding="utf-8")
    return str(_COOKIE_CACHE_PATH)


def build_ytdlp_common_opts() -> dict[str, Any]:
    opts: dict[str, Any] = {
        # Combining web+android reduces breakage across YouTube rollouts.
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "remote_components": ["ejs:github"],
    }

    cookiefile = _clean_env(getattr(settings, "YTDLP_COOKIES_FILE", "") or "")
    if not cookiefile:
        cookiefile = _materialize_cookie_file_from_env()

    if cookiefile and Path(cookiefile).exists():
        opts["cookiefile"] = cookiefile
    elif cookiefile:
        logger.warning("YTDLP cookiefile configured but not found: %s", cookiefile)

    return opts


def is_auth_challenge_error(message: str) -> bool:
    text = (message or "").lower()
    return "sign in to confirm you're not a bot" in text or "cookies" in text


def cookies_enabled() -> bool:
    cookiefile = _clean_env(getattr(settings, "YTDLP_COOKIES_FILE", "") or "")
    if cookiefile and Path(cookiefile).exists():
        return True
    return bool(
        _clean_env(os.environ.get("YTDLP_COOKIES_B64", ""))
        or _clean_env(os.environ.get("YTDLP_COOKIES_RAW", ""))
    )
