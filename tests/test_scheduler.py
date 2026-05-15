"""Tests for scan scheduler workflows."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.scans.models import Scan, ScanSchedule
from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email="sched@example.com", username="sched", password="testpass123")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="sched-admin@example.com", username="schedadmin", password="adminpass123", is_staff=True
    )


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(reverse("user-login"), {"email": user.email, "password": "testpass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    response = api_client.post(
        reverse("user-login"), {"email": admin_user.email, "password": "adminpass123"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def target(user):
    return Target.objects.create(owner=user, url="https://scheduler.example", verification_method="dns", verification_token="t")


@pytest.mark.django_db
class TestScanScheduler:
    def test_create_daily_weekly_custom_schedule(self, auth_client, target):
        now = timezone.now()
        for frequency in ["daily", "weekly", "custom"]:
            payload = {
                "target": target.id,
                "scan_type": "passive",
                "frequency": frequency,
                "custom_interval_minutes": 30,
                "next_run_at": (now - timedelta(minutes=1)).isoformat(),
                "queue_backend": "redis",
                "max_retries": 2,
            }
            response = auth_client.post(reverse("scan-schedule-list-create"), payload, format="json")
            assert response.status_code == status.HTTP_201_CREATED

    def test_enqueue_due_schedules(self, auth_client, admin_client, target, user):
        ScanSchedule.objects.create(
            owner=user,
            target=target,
            scan_type="active",
            frequency="daily",
            next_run_at=timezone.now() - timedelta(minutes=5),
            queue_backend="redis",
        )
        response = admin_client.post(reverse("scan-scheduler-enqueue"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["enqueued"] >= 1
        assert Scan.objects.filter(status="queued").exists()

    def test_worker_processes_queue(self, admin_client, target, user):
        Scan.objects.create(owner=user, target=target, scan_type="passive", status="queued", queue_backend="redis")
        response = admin_client.post(reverse("scan-scheduler-worker-run"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["processed"] is True
        scan = Scan.objects.get(id=response.data["scan_id"])
        assert scan.status == "completed"

    def test_retry_failed_scan_mechanism(self, admin_client, target, user, monkeypatch):
        scan = Scan.objects.create(
            owner=user,
            target=target,
            scan_type="passive",
            status="queued",
            queue_backend="rabbitmq",
            max_retries=1,
        )

        from apps.scans import views

        def fail_executor(_scan):
            raise RuntimeError("forced failure")

        monkeypatch.setattr(views, "_execute_scan", fail_executor)

        first = admin_client.post(reverse("scan-scheduler-worker-run"))
        assert first.status_code == status.HTTP_200_OK
        scan.refresh_from_db()
        assert scan.status == "queued"
        assert scan.retry_count == 1

        second = admin_client.post(reverse("scan-scheduler-worker-run"))
        assert second.status_code == status.HTTP_200_OK
        scan.refresh_from_db()
        assert scan.status == "failed"
        assert scan.retry_count == 2
