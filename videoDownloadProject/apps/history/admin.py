from django.contrib import admin
from .models import History

# Register your models here.
@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'job', 'job__video', 'success', 'job__completed_at']
    list_per_page = 20
    ordering = ['-job__completed_at']
    