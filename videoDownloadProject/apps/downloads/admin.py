from django.contrib import admin
from .models import DownloadJob

# Register your models here.
@admin.register(DownloadJob)
class DownloadJobAdmin(admin.ModelAdmin):
    list_display = ["output_filename", "user", "status", "video"]
    