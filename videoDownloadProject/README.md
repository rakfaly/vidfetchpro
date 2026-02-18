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
