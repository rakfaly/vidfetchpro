from django.urls import path
from . import views

app_name = 'apps.downloads'

urlpatterns = [
    path('', views.DownloadView.as_view(), name='index'),
    path('fetch/', views.fetch_metadata, name='fetch'),
    path('fetch/status/', views.fetch_status, name='fetch_status'),
]
