import os
from .settings import *  # noqa


DEBUG = False

def _parse_csv_env(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


ALLOWED_HOSTS = _parse_csv_env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = _parse_csv_env("CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = _parse_bool_env("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = _parse_bool_env("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = _parse_bool_env("CSRF_COOKIE_SECURE", True)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = _parse_bool_env("CSRF_COOKIE_HTTPONLY", False)
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")

SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _parse_bool_env(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", True
)
SECURE_HSTS_PRELOAD = _parse_bool_env("SECURE_HSTS_PRELOAD", True)
SECURE_CONTENT_TYPE_NOSNIFF = _parse_bool_env("SECURE_CONTENT_TYPE_NOSNIFF", True)
SECURE_REFERRER_POLICY = os.environ.get(
    "SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin"
)
X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "DENY")

# Honor HTTPS when running behind a reverse proxy/load balancer (Nginx, Render, etc.).
proxy_ssl_header_name = os.environ.get("SECURE_PROXY_SSL_HEADER_NAME", "").strip()
proxy_ssl_header_value = os.environ.get("SECURE_PROXY_SSL_HEADER_VALUE", "").strip()
if proxy_ssl_header_name and proxy_ssl_header_value:
    SECURE_PROXY_SSL_HEADER = (proxy_ssl_header_name, proxy_ssl_header_value)

USE_X_FORWARDED_HOST = _parse_bool_env("USE_X_FORWARDED_HOST", True)

# Production static files directory (for `collectstatic` outputs).
STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

# TASKS = {
#     "default": {
#         "BACKEND": os.environ.get(
#             "DJANGO_TASKS_BACKEND",
#             "django.tasks.backends.immediate.ImmediateBackend",
#         ),
#     }
# }

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "")
CELERY_TASK_ALWAYS_EAGER = False
