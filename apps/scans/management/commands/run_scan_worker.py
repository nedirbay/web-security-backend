"""Run scheduled scan worker loop."""
import time

from django.core.management.base import BaseCommand

from apps.scans.models import Scan
from apps.scans.services.scheduler_service import run_worker_once
from apps.scans.views import _execute_scan, _persist_vulnerabilities, _create_scan_notification


class Command(BaseCommand):
    help = "Run scan worker loop for queued jobs."

    def add_arguments(self, parser):
        parser.add_argument("--sleep", type=int, default=3, help="Sleep seconds between polling cycles.")
        parser.add_argument("--once", action="store_true", help="Run one cycle and exit.")

    def handle(self, *args, **options):
        sleep_seconds = options["sleep"]
        run_once = options["once"]

        while True:
            processed = run_worker_once(_execute_scan)
            if processed:
                processed.refresh_from_db()
                if processed.status in {Scan.Status.COMPLETED, Scan.Status.FAILED}:
                    _persist_vulnerabilities(processed)
                    _create_scan_notification(processed)
                    self.stdout.write(self.style.SUCCESS(f"Processed scan #{processed.id}: {processed.status}"))
            if run_once:
                return
            time.sleep(sleep_seconds)
