"""Tests for optional advanced scanning features."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.scans.models import Scan, Vulnerability
from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email="adv@example.com", username="adv", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(reverse("user-login"), {"email": user.email, "password": "testpass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def target(user):
    return Target.objects.create(owner=user, url="https://adv-target.example", verification_method="dns", verification_token="t")


@pytest.mark.django_db
class TestAdvancedFeatures:
    def test_api_scanning_postman_like(self, auth_client):
        response = auth_client.post(
            reverse("advanced-api-scan"),
            {"method": "POST", "path": "/api/admin/users", "headers": {}, "body": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "findings" in response.data

    def test_jwt_vulnerability_checks(self, auth_client):
        response = auth_client.post(reverse("advanced-jwt-check"), {"token": "not-a-jwt"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "issues" in response.data
        assert response.data["issues"]

    def test_graphql_security_scan(self, auth_client):
        response = auth_client.post(
            reverse("advanced-graphql-scan"),
            {"endpoint": "https://api.example/graphql", "query": "{ __schema { types { name } } }"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "findings" in response.data

    def test_header_analysis(self, auth_client):
        response = auth_client.get(
            reverse("advanced-header-analysis"),
            HTTP_CSP="default-src 'self'",
            HTTP_STRICT_TRANSPORT_SECURITY="max-age=31536000",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["csp_present"] is True
        assert response.data["hsts_present"] is True

    def test_ai_layer_summary(self, auth_client, user, target):
        scan = Scan.objects.create(owner=user, target=target, scan_type="passive", status="completed")
        Vulnerability.objects.create(scan=scan, target=target, owner=user, name="SQLi", severity="High", owasp_category="A03", url=target.url)
        response = auth_client.get(reverse("advanced-ai-summary"))
        assert response.status_code == status.HTTP_200_OK
        assert "risk_summary" in response.data
        assert "auto_fix_suggestions" in response.data
