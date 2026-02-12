#from django.shortcuts import render
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
        #user = getattr(self.request, "user", None)
        #if user and user.is_authenticated:
        #return queryset.filter(job__user=user).order_by("-created_at")
        #return queryset.none()
        
