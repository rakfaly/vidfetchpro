from django.shortcuts import render
from django.views.generic import ListView

from .models import History


# Create your views here.
class HistoryView(ListView):
    """History page showing completed download outcomes."""

    template_name = "history/history.html"
    context_object_name = "history_list"
    paginate_by = 20

    def get_queryset(self):
        queryset = History.objects.select_related("job", "job__video", "job__format")
        return queryset.order_by("-created_at")


def clear_history(request):
    if not request.htmx:
        return render(request, "history/history.html")
    if len(History.objects.all()) > 0:
        History.objects.all().delete()
    return render(request, "downloads/partials/history/list.html")
