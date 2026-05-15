"""Admin registrations for scans."""
from django.contrib import admin

from .models import Scan, ScanSchedule, ZapConfiguration


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "target", "owner", "scan_type", "status", "queue_backend", "created_at")
    list_filter = ("scan_type", "status", "proxy_enabled", "use_context", "queue_backend")
    search_fields = ("target__url", "owner__email", "zap_scan_id")


@admin.register(ZapConfiguration)
class ZapConfigurationAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "api_url", "timeout_seconds", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("owner__email", "api_url")


@admin.register(ScanSchedule)
class ScanScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "target", "scan_type", "frequency", "next_run_at", "is_enabled")
    list_filter = ("frequency", "is_enabled", "queue_backend")
    search_fields = ("owner__email", "target__url")
