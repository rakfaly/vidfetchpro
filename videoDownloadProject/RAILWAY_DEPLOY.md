# Railway Deployment Guide

This project deploys as 4 services in one Railway project:
- `web` (Django + Gunicorn)
- `worker` (Celery)
- `Postgres` (managed Railway PostgreSQL)
- `rabbitmq` (RabbitMQ service)

## 1) Create services
1. Create a new Railway project.
2. Add a `PostgreSQL` service from Railway databases.
3. Add a `rabbitmq` service:
   - Option A: one-click RabbitMQ template.
   - Option B: new service from image `rabbitmq:3.13-management-alpine`.
4. Add `web` service from this GitHub repo (Dockerfile deploy).
5. Add `worker` service from the same repo (Dockerfile deploy).

## 2) Configure start commands
Railway Service -> Settings -> Deploy -> Start Command.

`web` start command:
```sh
sh -lc "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120"
```

`worker` start command:
```sh
celery -A core worker -l info
```

## 3) Set environment variables
Use `.env.railway.example` as your checklist.

Set variables in both `web` and `worker`:
- `DJANGO_SETTINGS_MODULE=core.settings_prod`
- `DEBUG=False`
- `SECRET_KEY=<strong-random-secret>`
- `DB_NAME=${{Postgres.PGDATABASE}}`
- `DB_USER=${{Postgres.PGUSER}}`
- `DB_PASSWORD=${{Postgres.PGPASSWORD}}`
- `DB_HOST=${{Postgres.PGHOST}}`
- `DB_PORT=${{Postgres.PGPORT}}`
- `CELERY_RESULT_BACKEND=django-db`
- `CELERY_BROKER_URL=amqp://<user>:<pass>@rabbitmq.railway.internal:5672/%2f`
- `ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}`
- `CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}`
- SSL/proxy vars from `.env.railway.example`

Set on `web` service:
- `STATIC_ROOT=/app/staticfiles`

## 4) Networking and domains
1. Generate a public domain for `web` in Networking.
2. Keep `worker`, `Postgres`, and `rabbitmq` private.
3. Ensure the RabbitMQ hostname in `CELERY_BROKER_URL` matches your service name:
   - `<service-name>.railway.internal`

## 5) First deploy checks
1. Deploy `web` and `worker`.
2. Confirm `web` logs show migrations completed and Gunicorn started.
3. Confirm `worker` logs show it connected to broker and is ready.
4. Open `https://<your-railway-domain>/admin/`.

Create admin user once via Railway shell on `web`:
```sh
python manage.py createsuperuser
```

## 6) Media persistence (optional but recommended)
If downloads/uploads must persist across deploys:
- Attach a Railway Volume to `web` and `worker` at `/app/media`, or
- Move media to object storage (recommended for scale).

## 7) Common issues
- `DisallowedHost`: `ALLOWED_HOSTS` missing current domain.
- CSRF failures: `CSRF_TRUSTED_ORIGINS` missing `https://...` domain.
- Celery cannot connect: wrong RabbitMQ credentials or wrong `rabbitmq.railway.internal` service name.
- DB auth failure: `DB_*` vars not referencing the Railway Postgres service values.

## References
- Railway Docker deploys: https://docs.railway.com/builds/dockerfiles
- Railway start command: https://docs.railway.com/deployments/start-command
- Railway Postgres variables: https://docs.railway.com/databases/postgresql
- Railway private networking: https://docs.railway.com/guides/private-networking
- Railway domains and internal DNS: https://docs.railway.com/networking/domains
- RabbitMQ template: https://railway.com/template/_o12zG
