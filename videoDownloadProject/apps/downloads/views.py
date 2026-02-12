from django.views.generic import ListView

from apps.downloads.models import DownloadJob
from apps.downloads.tasks.fetch_metadata_tasks import enqueue_fetch_data
from apps.history.models import History
from django.shortcuts import redirect
from apps.downloads.forms import FetchMetadataForm
from celery.result import AsyncResult
from django.http import JsonResponse

class DownloadView(ListView):
    """Dashboard showing the download flow and recent jobs."""

    model = DownloadJob
    template_name = 'downloads/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context["fetch_form"] = FetchMetadataForm()
        context["fetched_data"] = None

        if user.is_authenticated:
            context["history_list"] = (
                History.objects
                .select_related("job", "job__video", "job__format")
                .filter(job__user=user)
                .order_by("-created_at")[:4]
            )
        else:
            context["history_list"] = []

        task_id = self.request.session.get("fetch_task_id")
        if task_id:
            result = AsyncResult(task_id)
            if result.successful():
                context["fetched_data"] = result.result
                self.request.session.pop("fetch_task_id", None)
        return context


def fetch_metadata(request):
    """Handle metadata fetch form submission."""
    if request.method != "POST":
        return redirect("apps.downloads:index")

    form = FetchMetadataForm(request.POST)
    if not form.is_valid():
        return redirect("apps.downloads:index")

    video_url = form.cleaned_data["video_url"]
    result = enqueue_fetch_data(video_url)
    # Store the tasks result in the session
    request.session["fetch_task_id"] = getattr(result, "id", None)
    return redirect("apps.downloads:index")


def fetch_status(request):
    """Handle metadata fetch status check."""
    task_id = request.session.get("fetch_task_id")
    if not task_id:
        return JsonResponse({"status": "none"})

    result = AsyncResult(task_id)
    if result.successful():
        request.session.pop("fetch_task_id", None)
        return JsonResponse({"status": "success", "data": result.result})
    if result.failed():
        return JsonResponse({"status": "error", "message": str(result.result)})
    return JsonResponse({"status": "pending"})
        
