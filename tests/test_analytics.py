"""Tests for analytics and statistics endpoints."""
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
    return User.objects.create_user(email="ana@example.com", username="ana", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(reverse("user-login"), {"email": user.email, "password": "testpass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def seed_data(user):
    t1 = Target.objects.create(owner=user, url="https://a.example", verification_method="dns", verification_token="1")
    t2 = Target.objects.create(owner=user, url="https://b.example", verification_method="dns", verification_token="2")

    s1 = Scan.objects.create(owner=user, target=t1, scan_type="passive", status="completed")
    s2 = Scan.objects.create(owner=user, target=t1, scan_type="active", status="failed")
    s3 = Scan.objects.create(owner=user, target=t2, scan_type="api", status="completed")

    Vulnerability.objects.create(scan=s1, target=t1, owner=user, name="SQL Injection", severity="High", owasp_category="A03", url=t1.url)
    Vulnerability.objects.create(scan=s1, target=t1, owner=user, name="SQL Injection", severity="High", owasp_category="A03", url=t1.url)
    Vulnerability.objects.create(scan=s2, target=t1, owner=user, name="XSS", severity="Medium", owasp_category="A03", url=t1.url)
    Vulnerability.objects.create(scan=s3, target=t2, owner=user, name="CSP Missing", severity="Low", owasp_category="A05", url=t2.url)
    return (s1, s2, s3)


@pytest.mark.django_db
class TestAnalytics:
    def test_vulnerability_trends(self, auth_client, seed_data):
        response = auth_client.get(reverse("analytics-vulnerability-trends"))
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

    def test_most_common_issues(self, auth_client, seed_data):
        response = auth_client.get(reverse("analytics-common-issues"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["name"] == "SQL Injection"

    def test_scan_success_rate(self, auth_client, seed_data):
        response = auth_client.get(reverse("analytics-scan-success-rate"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total"] == 3
        assert response.data["successful"] == 2

    def test_risk_heatmap_per_domain(self, auth_client, seed_data):
        response = auth_client.get(reverse("analytics-risk-heatmap"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_time_based_report_generation(self, auth_client, seed_data):
        response = auth_client.get(reverse("analytics-time-based-report"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["scan_total"] == 3
        assert response.data["vulnerability_total"] == 4
