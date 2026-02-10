from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import UserProfile

# Register your models here.
#@admin.register(UserProfile)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "profile__plan_tier", "profile__max_resolution", "is_staff"]
    inlines = [
        UserProfileInline
    ]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
