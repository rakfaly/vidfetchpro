# Video Download Project — Requirements (Dev)

**Audience:** Developers

## Overview
A Django-based web app that lets users paste a video URL, fetch metadata, select a format, and download the file. The frontend is HTML + Tailwind CSS + HTMX. The backend is Django with Celery + RabbitMQ for background download jobs. PostgreSQL is the database. Files are stored locally under `media/downloads/`.

## Goals
- Provide a smooth, professional download workflow (fetch → format → download → progress).
- Enforce limits for anonymous users while allowing full access for logged users.
- Track downloads, progress, and history.

## Tech Stack
- **Backend:** Django 6
- **Async Tasks:** Celery with RabbitMQ
- **Database:** PostgreSQL
- **Storage:** Local disk (`MEDIA_ROOT/downloads/`)
- **Frontend:** HTML, Tailwind CSS, JavaScript
- **Downloader:** yt-dlp

## Core Features
1. **Fetch metadata**
   - User pastes a URL and clicks Fetch.
   - Backend retrieves metadata from yt-dlp.
   - Store minimal structured fields + raw JSON for flexibility.

2. **Format selection**
   - User selects a format.
   - Store yt-dlp `format_id` for exact download.

3. **Download**
   - User clicks Download.
   - Start background job(s) (Celery).
   - Update progress: percent, speed, ETA, bytes downloaded.

4. **Download history**
   - Logged users can view recent completed/failed downloads.

5. **Limits**
   - Anonymous users: limited rate + limited max resolution.
   - Logged users: unlimited and higher resolutions.

## Data Model Summary (Apps)
- `apps/users`: `UserProfile` (plan tier, daily limit, max resolution, unlimited flag).
- `apps/videos`: `VideoSource`, `VideoFormat` (includes `format_id`).
- `apps/downloads`: `DownloadJob` (status + progress fields).
- `apps/history`: `DownloadHistory` (final outcome).
- `apps/common`: shared base models (timestamps).

## Download Flow
1. **Fetch**
   - Validate URL
   - Run yt-dlp metadata extraction
   - Persist `VideoSource` + `VideoFormat` list

2. **Format selection**
   - Store yt-dlp `format_id`
   - Render prepare download step

3. **Download**
   - Validate user plan
   - Create `DownloadJob` per entry (playlist supported)
   - Enqueue Celery task(s)
   - Track progress updates
   - Update job status on completion/failure

4. **Progress polling (HTMX)**
   - Poll the progress endpoint every second while any job is active
   - Stop polling when all jobs are completed/failed/cancelled

## Security Constraints
- Validate URLs (scheme + host allowlist).
- Restrict provider domains if required.
- Enforce rate limits for anonymous/free users.
- Deny premium-only formats for free users.
- Store only safe file names (sanitize output).
- Keep secrets in `.env` (never hardcode).

## Non-Functional Requirements
- Background tasks must not block HTTP requests.
- All long downloads must use Celery.
- System should tolerate missing metadata fields.

## Environments
- **Dev:** `core.settings_dev` (DEBUG on, immediate tasks optional).
- **Prod:** `core.settings_prod` (DEBUG off, secure cookies, HSTS).

## External Services
- **RabbitMQ** as Celery broker.
- No external storage yet (local disk only).

## File Structure (Relevant)
```
apps/
  users/
  videos/
  downloads/
    services/
    tasks/
  history/
  common/
core/
  settings_dev.py
  settings_prod.py
```

## Open Items (Future)
- Switch to S3 (or other cloud storage).
- Add API endpoints for frontend integration.
- Add auditing/logging for failed downloads.
