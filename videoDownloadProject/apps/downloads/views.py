from celery.result import AsyncResult
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView

from apps.downloads.forms import FetchMetadataForm
from apps.downloads.models import DownloadJob
from apps.downloads.services.playlist import (
    build_playlist_preview,
    launch_playlist_downloads,
)
from apps.downloads.tasks.fetch_metadata_tasks import enqueue_fetch_data
from apps.history.models import History
from utils import utils


class DownloadView(ListView):
    """Dashboard showing the download flow and recent jobs."""

    model = DownloadJob
    template_name = "downloads/index.html"

    def get_context_data(self, **kwargs):
        """
        Build template context for the dashboard.

        Adds:
        - `fetch_form`: the URL input form.
        - `history_list`: recent jobs for authenticated users.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user"] = user
        context["fetch_form"] = FetchMetadataForm()

        if user.is_authenticated:
            context["history_list"] = (
                History.objects.select_related("job", "job__video", "job__format")
                .filter(job__user=user)
                .order_by("-created_at")[:4]
            )
        else:
            context["history_list"] = []
        return context


def fetch_metadata(request):
    """
    Kick off metadata extraction for a submitted video URL.

    In POST + HTMX: enqueue fetch task and return spinner fragment.
    In other cases: redirect to dashboard.

    POST parameters:
    - `video_url`: URL to fetch metadata for.
    """
    if request.method != "POST":
        return redirect("apps.downloads:index")

    form = FetchMetadataForm(request.POST)
    if not form.is_valid():
        return redirect("apps.downloads:index")

    if request.htmx:
        video_url = form.cleaned_data["video_url"]
        info = enqueue_fetch_data(video_url)
        # Store the tasks result in the session
        request.session["fetch_task_id"] = getattr(info, "id", None)

        task_id = request.session.get("fetch_task_id")
        result = AsyncResult(task_id)
        return render(request, "downloads/fetched_spinner.html", {"task": result})

    return redirect("apps.downloads:index")


def fetch_status(request):
    """
    Poll the metadata fetch task and return the next fragment.

    In HTMX:
    - If task complete: returns fetched metadata + format choices.
    - If failed: returns an error badge.
    - Otherwise: returns the spinner fragment.
    """
    if request.htmx:
        task_id = request.session.get("fetch_task_id")
        if not task_id:
            return HttpResponse("")

        result = AsyncResult(task_id)

        if result.successful():
            entries, formats = build_playlist_preview(result.result)

            return render(
                request,
                "downloads/fetched_form.html",
                {
                    "fetched_data": entries,
                    "formats": formats,
                },
            )

        if result.failed():
            return HttpResponse(
                '<span class="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold '
                'text-red-700 dark:bg-red-500/20 dark:text-emerald-300">'
                "Failed to fetch metadata"
                "</span>"
            )
        return render(request, "downloads/fetched_spinner.html", {"task": result})
    return HttpResponse("")


def prepare_download(request):
    """
    Resolve the selected format and render the download step.

    In POST + HTMX: validates selected `format` and returns the
    prepare_download fragment with format title.
    """
    if request.method != "POST" or not request.htmx:
        return redirect("apps.downloads:index")

    fmt_id = request.POST.get("format")
    if not fmt_id:
        return HttpResponse("No format selected")

    task_id = request.session.get("fetch_task_id")
    if not task_id:
        return HttpResponse("")

    result = AsyncResult(task_id)
    if not result.successful():
        return HttpResponse("")

    _entries, formats = build_playlist_preview(result.result)
    fmt = next((f for f in formats if f.get("format_id") == fmt_id), None)
    if not fmt:
        return HttpResponse("Format not found")

    if _entries[0]:
        fmt_title = f"""{_entries[0].get("title", "Untitle")}.{fmt.get('ext', '')}
       ({' ' if fmt.get('height') else ''}{fmt.get('height', '')}p)""".strip()
    else:
        fmt_title = ""
    return render(
        request,
        "downloads/prepare_download.html",
        {"format_id": fmt_id, "format_title": fmt_title, "format": fmt},
    )


def start_download(request):
    """
    Launch download jobs for the selected format and return progress UI.

    In POST + HTMX:
    - Validates session task and format selection.
    - Starts jobs (single or playlist) for the chosen format.
    - Stores job IDs in session for progress polling.
    """
    if request.method != "POST" or not request.htmx:
        return redirect("apps.downloads:index")

    fmt_id = request.POST.get("format")
    if not fmt_id:
        return HttpResponse("No format selected")
    task_id = request.session.get("fetch_task_id")
    if not task_id:
        return HttpResponse("No task ID")

    result = AsyncResult(task_id)
    if not result.successful():
        return HttpResponse("No result")

    user = request.user
    if not user.is_authenticated:
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username="anonymous-user", defaults={"password": "anonymous-pass"}
        )
    jobs = launch_playlist_downloads(user, result.result, fmt_id)
    if not jobs:
        return HttpResponse("No jobs created (format_id mismatch or missing formats)")
    job_ids = [str(j.id) for j in jobs]
    request.session["download_job_id"] = job_ids[0]
    request.session["download_job_ids"] = job_ids
    job_id = job_ids[0]
    job = (
        DownloadJob.objects.filter(id=job_id).select_related("format", "video").first()
    )
    duration = utils.format_duration(job.eta_seconds) if job else None
    speed_kbps = None
    if job and job.speed_kbps:
        speed_kbps = utils.convert_bandwidth_binary(job.speed_kbps)
    elapsed = None
    if job and job.bytes_downloaded and job.bytes_total:
        elapsed = f"{utils.format_bytes(job.bytes_downloaded)}/{utils.format_bytes(job.bytes_total)}"
    return render(
        request,
        "downloads/prepare_download.html",
        {
            "format_id": fmt_id,
            "format_title": request.POST.get("format_title"),
            "download_started": True,
            "job_id": job_id,
            "poll": True,
            "download_progress": job.progress_percent if job else 0,
            "download_status": job.status if job else "queued",
            "download_eta": duration,
            "download_speed": speed_kbps,
            "download_elapsed": elapsed,
        },
    )


def progress_status(request):
    """
    Poll active download jobs and render progress fragment.

    Uses job IDs stored in session to find the first active job.
    Stops polling once all jobs are completed/failed/cancelled.
    """
    try:
        job_ids = request.session.get("download_job_ids") or []
        if not job_ids:
            return HttpResponse("")

        active_job = (
            DownloadJob.objects.filter(id__in=job_ids)
            .exclude(status="completed")
            .exclude(status="failed")
            .exclude(status="cancelled")
            .select_related("format", "video")
            .order_by("created_at")
            .first()
        )
        poll = True
        job = active_job
        if not job:
            last_job = (
                DownloadJob.objects.filter(id__in=job_ids)
                .select_related("format", "video")
                .order_by("-created_at")
                .first()
            )
            if not last_job:
                return HttpResponse("")
            job = last_job
            poll = False
        duration = utils.format_duration(job.eta_seconds)
        speed_kbps = None
        if job.speed_kbps:
            speed_kbps = utils.convert_bandwidth_binary(job.speed_kbps)
        elapsed = None
        if job.bytes_downloaded and job.bytes_total:
            elapsed = f"{utils.format_bytes(job.bytes_downloaded)}/{utils.format_bytes(job.bytes_total)}"
    except Exception as e:
        return HttpResponse("<p>Error: %s</p>" % e)

    return render(
        request,
        "downloads/progress_status.html",
        {
            "poll": poll,
            "job_id": str(job.id),
            "format_title": job.video.title if job.video else "",
            "download_progress": job.progress_percent,
            "download_status": job.status,
            "download_eta": duration,
            "download_speed": speed_kbps,
            "download_elapsed": elapsed,
        },
    )
