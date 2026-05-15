"""Scheduler and worker helpers for scan jobs."""
from datetime import timedelta

from django.utils import timezone

from apps.scans.models import Scan, ScanSchedule


def compute_next_run(schedule: ScanSchedule, from_time=None):
    now = from_time or timezone.now()
    if schedule.frequency == ScanSchedule.Frequency.DAILY:
        return now + timedelta(days=1)
    if schedule.frequency == ScanSchedule.Frequency.WEEKLY:
        return now + timedelta(weeks=1)
    return now + timedelta(minutes=schedule.custom_interval_minutes)


def enqueue_due_schedules(now=None):
    now = now or timezone.now()
    due = ScanSchedule.objects.filter(is_enabled=True, next_run_at__lte=now)
    count = 0
    for schedule in due:
        schedule.create_scan_job()
        schedule.next_run_at = compute_next_run(schedule, from_time=now)
        schedule.save(update_fields=["next_run_at", "updated_at"])
        count += 1
    return count


def run_worker_once(executor):
    queued = Scan.objects.filter(status=Scan.Status.QUEUED).order_by("created_at").first()
    if not queued:
        return None

    queued.status = Scan.Status.RUNNING
    queued.save(update_fields=["status", "updated_at"])

    try:
        executor(queued)
    except Exception:
        queued.retry_count += 1
        queued.status = Scan.Status.QUEUED if queued.retry_count <= queued.max_retries else Scan.Status.FAILED
        queued.save(update_fields=["retry_count", "status", "updated_at"])
        return queued

    queued.status = Scan.Status.COMPLETED
    queued.completed_at = timezone.now()
    queued.save(update_fields=["status", "completed_at", "updated_at", "zap_scan_id", "raw_results", "parsed_alerts"])
    return queued
