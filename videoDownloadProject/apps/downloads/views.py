from django.views.generic import ListView
from django.shortcuts import redirect, render
from celery.result import AsyncResult
from django.http import JsonResponse, HttpResponse
from apps.downloads.tasks.fetch_metadata_tasks import enqueue_fetch_data
from apps.downloads.forms import FetchMetadataForm
from apps.history.models import History
from apps.downloads.models import DownloadJob
from utils.utils import normalize_entry
from apps.downloads.services.playlist import build_playlist_preview, launch_playlist_downloads, _filtered_formats


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
            #return JsonResponse({'formats': formats[0]["height"]})
                

        if result.failed():
            return HttpResponse(
                '<span class="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold '
                'text-red-700 dark:bg-red-500/20 dark:text-emerald-300">'
                'Failed to fetch metadata'
                '</span>'
            )
        return render(request, "downloads/fetched_spinner.html", {"task": result})
    return HttpResponse("")
