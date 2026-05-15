"""Tests for API layer concerns: docs, validation, and throttling."""
import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAPILayer:
    def test_openapi_schema_endpoint(self, api_client):
        response = api_client.get(reverse("openapi-schema"))
        assert response.status_code == status.HTTP_200_OK
        assert "paths" in response.data
        assert "/api/users/register/" in response.data["paths"]
        assert "/api/scans/" in response.data["paths"]

    def test_swagger_ui_endpoint(self, api_client):
        response = api_client.get(reverse("swagger-ui"))
        assert response.status_code == status.HTTP_200_OK
        assert "swagger-ui" in response.content.decode("utf-8")

    def test_request_validation_error_on_register(self, api_client):
        response = api_client.post(
            reverse("user-register"),
            {"email": "invalid-email", "password": "x", "password_confirm": "y"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rate_limiting_is_configured(self, api_client):
        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", ())
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        assert "rest_framework.throttling.AnonRateThrottle" in throttle_classes
        assert "apps.core.throttling.UserRateThrottleWithAdminBypass" in throttle_classes
        assert throttle_rates.get("anon")
        assert throttle_rates.get("user")
