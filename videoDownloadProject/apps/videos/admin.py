from django.contrib import admin
from .models import VideoSource

# Register your models here.
@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ["title", "channel_name", "duration_seconds"]