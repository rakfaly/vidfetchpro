from django.urls import path

from .views import HistoryView, clear_history

app_name = "apps.history"

urlpatterns = [
    path("", HistoryView.as_view(), name="history"),
    path("clear-history", clear_history, name="clear_history"),
]
