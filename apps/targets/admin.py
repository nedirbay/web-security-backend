"""Admin registrations for targets."""
from django.contrib import admin

from .models import Target


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "owner", "verification_status", "is_active", "created_at")
    list_filter = ("verification_status", "is_active", "verification_method")
    search_fields = ("url", "owner__email", "owner__username")
