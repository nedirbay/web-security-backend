"""Tests for admin panel APIs."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import AuditLog, Role, SystemSetting
from apps.scans.models import Scan, Vulnerability
from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="panel-admin@example.com",
        username="paneladmin",
        password="adminpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def normal_user():
    return User.objects.create_user(email="panel-user@example.com", username="paneluser", password="testpass123")


@pytest.fixture
def admin_client(api_client, admin_user):
    response = api_client.post(
        reverse("user-login"), {"email": admin_user.email, "password": "adminpass123"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def auth_client(api_client, normal_user):
    response = api_client.post(
        reverse("user-login"), {"email": normal_user.email, "password": "testpass123"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.mark.django_db
class TestAdminPanel:
    def test_admin_dashboard(self, admin_client, normal_user):
        target = Target.objects.create(owner=normal_user, url="https://dash.example", verification_method="dns", verification_token="t")
        scan = Scan.objects.create(owner=normal_user, target=target, scan_type="passive", status="failed")
        Vulnerability.objects.create(
            scan=scan,
            target=target,
            owner=normal_user,
            name="SQLi",
            severity="High",
            owasp_category="A03",
            url=target.url,
        )

        response = admin_client.get(reverse("admin-dashboard"))
        assert response.status_code == status.HTTP_200_OK
        assert "total_scans" in response.data
        assert "critical_vulnerabilities" in response.data

    def test_admin_user_management_role_and_suspend(self, admin_client, normal_user):
        role = Role.objects.create(name="analyst", description="Analyst")
        response = admin_client.patch(
            reverse("admin-user-manage", kwargs={"pk": normal_user.id}),
            {"role_id": role.id, "is_active": False},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        normal_user.refresh_from_db()
        assert normal_user.role_id == role.id
        assert normal_user.is_active is False

    def test_admin_assign_target(self, admin_client, normal_user):
        other = User.objects.create_user(email="other@example.com", username="other", password="testpass123")
        target = Target.objects.create(owner=other, url="https://assign-admin.example", verification_method="dns", verification_token="x")
        response = admin_client.post(
            reverse("admin-assign-target", kwargs={"pk": normal_user.id}),
            {"target_id": target.id},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.owner_id == normal_user.id

    def test_system_settings_and_audit_logs(self, admin_client):
        create_response = admin_client.post(
            reverse("admin-setting-list-create"),
            {"key": "maintenance_mode", "value": "off", "description": "maintenance switch"},
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        setting_id = create_response.data["id"]

        update_response = admin_client.patch(
            reverse("admin-setting-detail", kwargs={"pk": setting_id}),
            {"value": "on"},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert SystemSetting.objects.get(id=setting_id).value == "on"

        logs_response = admin_client.get(reverse("admin-audit-log-list"))
        assert logs_response.status_code == status.HTTP_200_OK
        assert AuditLog.objects.count() >= 2

    def test_non_admin_forbidden(self, auth_client):
        response = auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == status.HTTP_403_FORBIDDEN
