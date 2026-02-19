from django.contrib import admin
from .models import DownloadJob

# Register your models here.
@admin.register(DownloadJob)
class DownloadJobAdmin(admin.ModelAdmin):
    list_display = ["video", "user", "status", "created_at"]
    list_per_page = 20
    #list_display_links = ["user"]
    readonly_fields = ["started_at", "completed_at"]
    ordering = ["-created_at"]
    