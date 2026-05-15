"""Models for scan management, scheduler and ZAP integration."""
from django.conf import settings
from django.db import models

from apps.targets.models import Target


class Scan(models.Model):
    class ScanType(models.TextChoices):
        PASSIVE = "passive", "Passive"
        ACTIVE = "active", "Active"
        FULL = "full", "Full"
        API = "api", "API"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scans")
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="scans")
    scan_type = models.CharField(max_length=10, choices=ScanType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    depth = models.PositiveIntegerField(default=1)
    attack_strength = models.CharField(max_length=20, default="medium")
    use_context = models.BooleanField(default=False)

    proxy_enabled = models.BooleanField(default=False)
    proxy_host = models.CharField(max_length=255, blank=True)
    proxy_port = models.PositiveIntegerField(null=True, blank=True)

    queue_backend = models.CharField(max_length=20, default="redis")
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    zap_scan_id = models.CharField(max_length=64, blank=True)
    raw_results = models.JSONField(default=dict, blank=True)
    parsed_alerts = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Vulnerability(models.Model):
    class Severity(models.TextChoices):
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"
        INFO = "Info", "Info"

    class LifecycleStatus(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWED = "reviewed", "Reviewed"
        FIXED = "fixed", "Fixed"
        CLOSED = "closed", "Closed"

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="vulnerabilities")
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="vulnerabilities")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vulnerabilities")
    name = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    owasp_category = models.CharField(max_length=255, default="Unknown")
    url = models.URLField(max_length=500)
    is_false_positive = models.BooleanField(default=False)
    lifecycle_status = models.CharField(max_length=10, choices=LifecycleStatus.choices, default=LifecycleStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class ZapConfiguration(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="zap_configs")
    api_url = models.URLField(default="http://localhost:8080")
    api_key = models.CharField(max_length=255, blank=True)
    timeout_seconds = models.PositiveIntegerField(default=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ScanSchedule(models.Model):
    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        CUSTOM = "custom", "Custom"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scan_schedules")
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="scan_schedules")
    scan_type = models.CharField(max_length=10, choices=Scan.ScanType.choices, default=Scan.ScanType.PASSIVE)
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    custom_interval_minutes = models.PositiveIntegerField(default=60)
    next_run_at = models.DateTimeField()
    is_enabled = models.BooleanField(default=True)
    queue_backend = models.CharField(max_length=20, default="redis")
    max_retries = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_run_at"]

    def create_scan_job(self):
        return Scan.objects.create(
            owner=self.owner,
            target=self.target,
            scan_type=self.scan_type,
            status=Scan.Status.QUEUED,
            queue_backend=self.queue_backend,
            max_retries=self.max_retries,
        )
