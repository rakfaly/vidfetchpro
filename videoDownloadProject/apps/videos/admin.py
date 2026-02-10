from django.contrib import admin
from .models import VideoSource, VideoFormat


# class VideoFormatInline(admin.StackedInline):
class VideoFormatInline(admin.TabularInline):
    model = VideoFormat
    pk_name = "formats"
    extra = 2
    exclude = ["format_id", "codec_video", "codec_audio"]
    ordering = ["-width"]
    raw_id_fields = ["video"]

# Register your models here.
@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ["title", "channel_name", "duration_seconds", "created_at"]
    list_filter = ["created_at"]
    readonly_fields = ["canonical_url", "thumbnail_url"]
    ordering = ["-created_at"]
    fieldsets = [
        (
            None, 
            {
                "fields": ["canonical_url", "channel_name", "title", "duration_seconds"]
            },
        ),
        (
            "Metadata",
            {
                "classes": ["wide","collapse"],
                "fields": ["provider", "thumbnail_url", ],
            }
        )
        
    ]
    inlines = [
        VideoFormatInline
    ]
    