"""Tests for results and vulnerabilities workflows."""
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
    return User.objects.create_user(email="vuln@example.com", username="vulnuser", password="testpass123")


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(reverse("user-login"), {"email": user.email, "password": "testpass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def target(user):
    return Target.objects.create(owner=user, url="https://vuln-target.example", verification_method="dns", verification_token="v1")


@pytest.fixture
def completed_scan(user, target):
    return Scan.objects.create(owner=user, target=target, scan_type="passive", status="completed")


@pytest.mark.django_db
class TestResultsAndVulnerabilities:
    def test_store_scan_results_in_database(self, auth_client, user, target):
        scan = Scan.objects.create(owner=user, target=target, scan_type="passive")
        response = auth_client.post(reverse("scan-run", kwargs={"pk": scan.id}))

        assert response.status_code == status.HTTP_200_OK
        scan.refresh_from_db()
        assert scan.raw_results != {}
        assert isinstance(scan.parsed_alerts, list)
        vuln_count = Vulnerability.objects.filter(scan=scan).count()
        if scan.parsed_alerts:
            assert vuln_count >= 1

    def test_filter_by_severity(self, auth_client, completed_scan, user, target):
        Vulnerability.objects.create(
            scan=completed_scan,
            target=target,
            owner=user,
            name="SQL Injection",
            severity="High",
            owasp_category="A03:2021-Injection",
            url=target.url,
        )
        Vulnerability.objects.create(
            scan=completed_scan,
            target=target,
            owner=user,
            name="CSP Missing",
            severity="Low",
            owasp_category="A05:2021-Security Misconfiguration",
            url=target.url,
        )

        response = auth_client.get(reverse("vulnerability-list"), {"severity": "High"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["severity"] == "High"

    def test_group_by_owasp_category(self, auth_client, completed_scan, user, target):
        Vulnerability.objects.create(
            scan=completed_scan,
            target=target,
            owner=user,
            name="XSS",
            severity="Medium",
            owasp_category="A03:2021-Injection",
            url=target.url,
        )
        Vulnerability.objects.create(
            scan=completed_scan,
            target=target,
            owner=user,
            name="SQLi",
            severity="High",
            owasp_category="A03:2021-Injection",
            url=target.url,
        )

        response = auth_client.get(reverse("vulnerability-group-owasp"))
        assert response.status_code == status.HTTP_200_OK
        assert any(item["owasp_category"] == "A03:2021-Injection" and item["count"] >= 2 for item in response.data)

    def test_false_positive_marking(self, auth_client, completed_scan, user, target):
        vuln = Vulnerability.objects.create(
            scan=completed_scan,
            target=target,
            owner=user,
            name="Header Missing",
            severity="Info",
            owasp_category="A05:2021-Security Misconfiguration",
            url=target.url,
        )

        response = auth_client.post(reverse("vulnerability-false-positive", kwargs={"pk": vuln.id}))
        assert response.status_code == status.HTTP_200_OK
        vuln.refresh_from_db()
        assert vuln.is_false_positive is True

    def test_vulnerability_lifecycle_flow(self, auth_client, completed_scan, user, target):
        vuln = Vulnerability.objects.create(
            scan=completed_scan,
            target=target,
            owner=user,
            name="Open Redirect",
            severity="Medium",
            owasp_category="A01:2021-Broken Access Control",
            url=target.url,
        )

        for lifecycle in ["reviewed", "fixed", "closed"]:
            response = auth_client.post(
                reverse("vulnerability-lifecycle", kwargs={"pk": vuln.id}),
                {"status": lifecycle},
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK

        vuln.refresh_from_db()
        assert vuln.lifecycle_status == "closed"
