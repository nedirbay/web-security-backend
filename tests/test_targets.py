"""Tests for target management functionality."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.targets.models import Target

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="user@example.com",
        username="user1",
        password="testpass123",
    )


@pytest.fixture
def second_user():
    return User.objects.create_user(
        email="second@example.com",
        username="user2",
        password="testpass123",
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com",
        username="admin",
        password="adminpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(
        reverse("user-login"),
        {"email": "user@example.com", "password": "testpass123"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    response = api_client.post(
        reverse("user-login"),
        {"email": "admin@example.com", "password": "adminpass123"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.mark.django_db
class TestTargetManagement:
    def test_add_target_url(self, auth_client):
        response = auth_client.post(
            reverse("target-list-create"),
            {"url": "https://example.com", "verification_method": "dns"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["url"] == "https://example.com"
        assert response.data["verification_status"] == "pending"
        assert response.data["owner"] > 0

    def test_remove_target_url(self, auth_client, user):
        target = Target.objects.create(
            owner=user,
            url="https://remove.me",
            verification_method="dns",
            verification_token="token123",
        )

        response = auth_client.delete(reverse("target-detail", kwargs={"pk": target.id}))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Target.objects.filter(id=target.id).exists()

    def test_verify_domain_ownership(self, auth_client, user):
        target = Target.objects.create(
            owner=user,
            url="https://verify.me",
            verification_method="file",
            verification_token="verifytoken",
        )

        response = auth_client.post(
            reverse("target-verify-ownership", kwargs={"pk": target.id}),
            {"token": "verifytoken"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.verification_status == "verified"

    def test_enable_disable_scanning(self, auth_client, user):
        target = Target.objects.create(
            owner=user,
            url="https://toggle.me",
            verification_method="dns",
            verification_token="toggletoken",
        )

        response_disable = auth_client.post(reverse("target-toggle-active", kwargs={"pk": target.id}))
        assert response_disable.status_code == status.HTTP_200_OK
        assert response_disable.data["is_active"] is False

        response_enable = auth_client.post(reverse("target-toggle-active", kwargs={"pk": target.id}))
        assert response_enable.status_code == status.HTTP_200_OK
        assert response_enable.data["is_active"] is True

    def test_assign_target_to_user_admin_only(self, admin_client, user, second_user):
        target = Target.objects.create(
            owner=user,
            url="https://assign.me",
            verification_method="dns",
            verification_token="assigntoken",
        )

        response = admin_client.post(
            reverse("target-assign-owner", kwargs={"pk": target.id}),
            {"user_id": second_user.id},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.owner_id == second_user.id

    def test_non_admin_cannot_assign_target(self, auth_client, user):
        target = Target.objects.create(
            owner=user,
            url="https://cannot-assign.me",
            verification_method="dns",
            verification_token="cantassigntoken",
        )

        response = auth_client.post(
            reverse("target-assign-owner", kwargs={"pk": target.id}),
            {"user_id": user.id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
