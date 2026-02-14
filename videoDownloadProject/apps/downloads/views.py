from django.views.generic import ListView
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from celery.result import AsyncResult
from django.http import JsonResponse, HttpResponse
from apps.downloads.tasks.fetch_metadata_tasks import enqueue_fetch_data
from apps.downloads.forms import FetchMetadataForm
from apps.history.models import History
from apps.downloads.models import DownloadJob
from apps.downloads.services.playlist import build_playlist_preview, launch_playlist_downloads
from utils import utils



class DownloadView(ListView):
    """Dashboard showing the download flow and recent jobs."""

    model = DownloadJob
    template_name = 'downloads/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context["fetch_form"] = FetchMetadataForm()

        if user.is_authenticated:
            context["history_list"] = (
                History.objects
                .select_related("job", "job__video", "job__format")
                .filter(job__user=user)
                .order_by("-created_at")[:4]
            )
        else:
            context["history_list"] = []
        
        return context

        
def fetch_metadata(request):
    """Handle metadata fetch form submission."""
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
    if request.htmx:
        task_id = request.session.get("fetch_task_id")
        if not task_id:
            return HttpResponse("")
    
        result = AsyncResult(task_id)

        print("Task state:", result.state)
       
        if result.successful():
            (entries, formats) = build_playlist_preview(result.result)

            return render(request, "downloads/fetched_form.html", 
                {
                    "fetched_data": entries,
                    "formats": formats,
                })

        if result.failed():
            return HttpResponse(
                '<span class="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold '
                'text-red-700 dark:bg-red-500/20 dark:text-emerald-300">'
                'Failed to fetch metadata'
                '</span>'
            )
        return render(request, "downloads/fetched_spinner.html", {"task": result})
    return HttpResponse("")


def prepare_download(request):
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

    (_entries, formats) = build_playlist_preview(result.result)
    fmt = next((f for f in formats if f.get("format_id") == fmt_id), None)
    if not fmt:
        return HttpResponse("Format not found")

    if _entries[0]:
        fmt_title = f"{_entries[0].get("title", "Untitle")}.{fmt.get('ext', '')}({' ' if fmt.get('height') else ''}{fmt.get('height', '')}p)".strip()
    
    return render(
        request,
        "downloads/prepare_download.html",
        {"format_id": fmt_id, "format_title": fmt_title, "format": fmt},
    )


def start_download(request):
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
    job_id = jobs[0].id
    request.session["download_job_id"] = str(job_id)
    return render(
        request,
        "downloads/prepare_download.html",
        {
            "format_id": fmt_id,
            "format_title": request.POST.get("format_title"),
            "download_started": True,
            "job_id": job_id,
        },
    )


def progress_status(request):
    try:
        job_id = request.GET.get("job_id") or request.session.get("download_job_id")
        if not job_id:
            return HttpResponse("")

        job = DownloadJob.objects.filter(id=job_id).select_related("format").first()
        if not job:
            return HttpResponse("")
        duration = utils.format_duration(job.eta_seconds)
        speed_kbps = None
        if job.speed_kbps:
            speed_kbps = utils.convert_bandwidth_binary(job.speed_kbps)
        size_left = None
        if job.bytes_downloaded and job.bytes_total:
            size_left = f"{utils.format_bytes(job.bytes_downloaded)}/{utils.format_bytes(job.bytes_total)}"
    except Exception as e:
        return HttpResponse("<p>Error: %s</p>" % e)
    
    return render(
        request,
        "downloads/progress_status.html",
        {
            "job_id": job.id,
            "format_title": job.video.title if job.video else "",
            "download_progress": job.progress_percent,
            "download_status": job.status,
            "download_eta": duration,
            "download_speed": speed_kbps,
            "download_elapsed": size_left,
        },
    )
    
