from django.urls import path

from .views import HistoryView

app_name = 'apps.history'

urlpatterns = [
    path('', HistoryView.as_view(), name='history'),
]
