"""Tests for automated scanning flow (queue + worker + notifications)."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Notification
from apps.scans.models import Scan, ScanSchedule
from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email="auto@example.com", username="autouser", password="testpass123")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="auto-admin@example.com", username="autoadmin", password="adminpass123", is_staff=True
    )


@pytest.fixture
def target(user):
    return Target.objects.create(owner=user, url="https://auto.example", verification_method="dns", verification_token="t")


@pytest.fixture
def admin_client(api_client, admin_user):
    response = api_client.post(
        reverse("user-login"), {"email": admin_user.email, "password": "adminpass123"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.mark.django_db
class TestAutomatedScanning:
    def test_rabbitmq_schedule_publishes_job(self, admin_client, user, target, monkeypatch):
        published = {"count": 0}

        def fake_publish(scan_id):
            published["count"] += 1
            return True

        monkeypatch.setattr("apps.scans.services.scheduler_service.publish_scan_job", fake_publish)

        ScanSchedule.objects.create(
            owner=user,
            target=target,
            scan_type="active",
            frequency="daily",
            next_run_at=timezone.now() - timedelta(minutes=5),
            queue_backend="rabbitmq",
        )
        response = admin_client.post(reverse("scan-scheduler-enqueue"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["enqueued"] == 1
        assert published["count"] == 1

    def test_worker_creates_notification_after_processing(self, admin_client, user, target):
        scan = Scan.objects.create(owner=user, target=target, scan_type="passive", status="queued", queue_backend="redis")
        response = admin_client.post(reverse("scan-scheduler-worker-run"))
        assert response.status_code == status.HTTP_200_OK
        scan.refresh_from_db()
        assert scan.status == "completed"
        note = Notification.objects.filter(user=user).order_by("-id").first()
        assert note is not None
        assert f"Scan #{scan.id}" in note.message

    def test_run_scan_worker_command_once(self, user, target):
        Scan.objects.create(owner=user, target=target, scan_type="passive", status="queued", queue_backend="redis")
        call_command("run_scan_worker", once=True)
        assert Scan.objects.filter(owner=user, status="completed").exists()
