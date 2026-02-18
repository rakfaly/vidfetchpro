# Video Download Project

## Overview
Django app that lets users paste a video URL, fetch metadata, choose a format, and download with live progress. The UI uses HTMX to step through fetch → formats → download and to poll progress updates.

## Stack
- Django 6
- Celery + RabbitMQ
- PostgreSQL
- yt-dlp
- Tailwind CSS + HTMX

## Key Flows
1. Fetch metadata
2. Choose a format (stores yt-dlp `format_id`)
3. Start download
4. Poll progress (percent, status, speed, ETA)
5. Create account redirects to dashboard and shows an HTMX toast near navbar

## Progress Polling
The UI polls `/downloads/fetch/start-download/progress-status` every second while any job is active. When all jobs finish, polling stops.

## Development
Prereqs:
- PostgreSQL running locally (`videodldb`)
- RabbitMQ running locally

Setup:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run:
```bash
python manage.py migrate
python manage.py runserver
```

Worker:
```bash
celery -A core worker -l info
```

## Production Settings
Use `core.settings_prod` in production and provide environment variables.

Required:
- `SECRET_KEY` (long random value, not Django default)
- `ALLOWED_HOSTS` (comma-separated, e.g. `app.example.com,www.example.com`)
- `CSRF_TRUSTED_ORIGINS` (comma-separated HTTPS origins, e.g. `https://app.example.com`)
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `SUBSCRIPTION_WEBHOOK_SECRET` (shared secret for provider event endpoint)

Recommended:
- `SECURE_PROXY_SSL_HEADER_NAME=HTTP_X_FORWARDED_PROTO`
- `SECURE_PROXY_SSL_HEADER_VALUE=https`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`
- `STATIC_ROOT=/path/to/staticfiles`

## Project Structure
```
apps/
  downloads/
  users/
    forms/
      auth.py
      account.py
      security.py
    views/
      auth.py
      account.py
      security.py
    urls/
      auth.py
      account.py
      security.py
  videos/
  history/
  common/
core/
templates/
static/
```
