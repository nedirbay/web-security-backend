"""Tests for scanner integration (OWASP ZAP) workflows."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.scans.models import Scan
from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email="scanuser@example.com", username="scanuser", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(
        reverse("user-login"), {"email": "scanuser@example.com", "password": "testpass123"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def target(user):
    return Target.objects.create(
        owner=user,
        url="https://scan-target.example",
        verification_method="dns",
        verification_token="verify123",
    )


@pytest.mark.django_db
class TestScannerIntegration:
    def test_create_scan_with_type(self, auth_client, target):
        response = auth_client.post(
            reverse("scan-list-create"),
            {
                "target": target.id,
                "scan_type": "passive",
                "depth": 2,
                "attack_strength": "high",
                "use_context": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["scan_type"] == "passive"

    def test_supported_scan_types(self, auth_client, target):
        for scan_type in ["passive", "active", "full", "api"]:
            response = auth_client.post(
                reverse("scan-list-create"),
                {"target": target.id, "scan_type": scan_type},
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

    def test_scan_configuration_and_proxy_settings(self, auth_client, target):
        response = auth_client.post(
            reverse("scan-list-create"),
            {
                "target": target.id,
                "scan_type": "active",
                "depth": 3,
                "attack_strength": "low",
                "use_context": True,
                "proxy_enabled": True,
                "proxy_host": "127.0.0.1",
                "proxy_port": 8081,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["proxy_enabled"] is True
        assert response.data["proxy_port"] == 8081

    def test_run_spider_scan(self, auth_client, target):
        scan = Scan.objects.create(owner=target.owner, target=target, scan_type="passive")
        response = auth_client.post(reverse("scan-run", kwargs={"pk": scan.id}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "completed"
        assert response.data["zap_scan_id"].startswith("spider-")

    def test_run_active_scan(self, auth_client, target):
        scan = Scan.objects.create(owner=target.owner, target=target, scan_type="active", attack_strength="high")
        response = auth_client.post(reverse("scan-run", kwargs={"pk": scan.id}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["zap_scan_id"].startswith("active-")

    def test_results_parsing_alert_mapping(self, auth_client, target):
        scan = Scan.objects.create(owner=target.owner, target=target, scan_type="api")
        response = auth_client.post(reverse("scan-run", kwargs={"pk": scan.id}))

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["parsed_alerts"], list)
        assert len(response.data["parsed_alerts"]) >= 1
        first = response.data["parsed_alerts"][0]
        assert "risk" in first
        assert "url" in first
