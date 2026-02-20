from django.urls import path

from . import views

app_name = "apps.downloads"

urlpatterns = [
    path("", views.DownloadView.as_view(), name="index"),
    path("history", views.history, name="history"),
    path("fetch/", views.fetch_metadata, name="fetch"),
    path("fetch/status/", views.fetch_status, name="fetch_status"),
    path("fetch/prepare-download/", views.prepare_download, name="prepare_download"),
    path("fetch/start-download/", views.start_download, name="start_download"),
    path(
        "fetch/start-download/progress-status",
        views.progress_status,
        name="progress_status",
    ),
    path(
        "fetch/spinner-dummy",
        views.start_download_spinner,
        name="start_download_spinner",
    ),
    path("fetch/refresh-formats", views.refresh_formats, name="refresh_formats"),
    path("download/<uuid:job_id>/", views.download_file, name="download_file"),
]
