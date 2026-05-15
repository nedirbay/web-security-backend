"""Security tests: tenant isolation, admin IP controls, sanitization, and headers."""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.throttling import UserRateThrottleWithAdminBypass
from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a():
    return User.objects.create_user(email="a@example.com", username="auser", password="testpass123")


@pytest.fixture
def user_b():
    return User.objects.create_user(email="b@example.com", username="buser", password="testpass123")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="sec-admin@example.com", username="secadmin", password="adminpass123", is_staff=True, is_superuser=True
    )


@pytest.fixture
def auth_client_a(api_client, user_a):
    response = api_client.post(reverse("user-login"), {"email": user_a.email, "password": "testpass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def auth_client_b(api_client, user_b):
    response = api_client.post(reverse("user-login"), {"email": user_b.email, "password": "testpass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    response = api_client.post(
        reverse("user-login"), {"email": admin_user.email, "password": "adminpass123"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.mark.django_db
class TestSecurity:
    def test_multi_tenant_isolation_targets(self, auth_client_b, user_a):
        target_a = Target.objects.create(
            owner=user_a, url="https://tenant-a.example", verification_method="dns", verification_token="t"
        )
        response = auth_client_b.get(reverse("target-detail", kwargs={"pk": target_a.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @override_settings(SECURE_HSTS_SECONDS=3600)
    def test_security_headers_present(self, api_client):
        response = api_client.get(reverse("swagger-ui"), secure=True)
        assert response.status_code == status.HTTP_200_OK
        assert "Content-Security-Policy" in response
        assert response["Strict-Transport-Security"].startswith("max-age=3600")

    @override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"user": "1/minute"}})
    def test_admin_unlimited_throttle(self, admin_user):
        throttle = UserRateThrottleWithAdminBypass()
        request = type(
            "Req",
            (),
            {
                "user": admin_user,
                "META": {"REMOTE_ADDR": "127.0.0.1"},
            },
        )()
        assert throttle.allow_request(request, view=None) is True

    @override_settings()
    def test_admin_ip_whitelist_blocks_non_whitelisted(self, admin_client, monkeypatch):
        monkeypatch.setenv("ADMIN_IP_WHITELIST", "127.0.0.1")
        response = admin_client.get(reverse("admin-dashboard"), REMOTE_ADDR="10.0.0.55")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_input_sanitization_profile(self, auth_client_a, user_a):
        response = auth_client_a.patch(
            reverse("user-profile"),
            {"first_name": "<script>x</script>A", "bio": "<b>hello</b> world"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user_a.refresh_from_db()
        assert user_a.first_name == "xA"
        assert "b>" not in response.data["bio"]
