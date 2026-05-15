"""Tests for blog and documentation APIs."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import BlogPost, DocumentationPage

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="content-admin@example.com",
        username="contentadmin",
        password="adminpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def normal_user():
    return User.objects.create_user(email="content-user@example.com", username="contentuser", password="testpass123")


@pytest.fixture
def admin_client(api_client, admin_user):
    client = APIClient()
    response = client.post(
        reverse("user-login"), {"email": admin_user.email, "password": "adminpass123"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def user_client(api_client, normal_user):
    client = APIClient()
    response = client.post(
        reverse("user-login"), {"email": normal_user.email, "password": "testpass123"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.mark.django_db
class TestBlogDocs:
    def test_blog_post_crud_and_filters(self, admin_client, user_client, admin_user):
        create = admin_client.post(
            reverse("blog-post-list-create"),
            {
                "title": "OWASP XSS",
                "slug": "owasp-xss",
                "content": "xss details",
                "tags": "xss,owasp",
                "status": "published",
            },
            format="json",
        )
        assert create.status_code == status.HTTP_201_CREATED
        post_id = create.data["id"]
        assert BlogPost.objects.get(id=post_id).author_id == admin_user.id

        list_resp = user_client.get(reverse("blog-post-list-create"), {"search": "xss", "tag": "owasp"})
        assert list_resp.status_code == status.HTTP_200_OK
        assert list_resp.data["count"] >= 1

        update = admin_client.patch(reverse("blog-post-detail", kwargs={"pk": post_id}), {"title": "Updated"}, format="json")
        assert update.status_code == status.HTTP_200_OK

        delete = admin_client.delete(reverse("blog-post-detail", kwargs={"pk": post_id}))
        assert delete.status_code == status.HTTP_204_NO_CONTENT

    def test_docs_page_crud_and_filters(self, admin_client, user_client):
        create = admin_client.post(
            reverse("docs-page-list-create"),
            {
                "title": "API Security Basics",
                "slug": "api-security-basics",
                "category": "api",
                "content": "doc body",
                "is_published": True,
            },
            format="json",
        )
        assert create.status_code == status.HTTP_201_CREATED
        page_id = create.data["id"]
        assert DocumentationPage.objects.filter(id=page_id).exists()

        list_resp = user_client.get(reverse("docs-page-list-create"), {"search": "security", "category": "api"})
        assert list_resp.status_code == status.HTTP_200_OK
        assert list_resp.data["count"] >= 1

        update = admin_client.patch(reverse("docs-page-detail", kwargs={"pk": page_id}), {"title": "API Security 101"}, format="json")
        assert update.status_code == status.HTTP_200_OK

        delete = admin_client.delete(reverse("docs-page-detail", kwargs={"pk": page_id}))
        assert delete.status_code == status.HTTP_204_NO_CONTENT

    def test_non_admin_cannot_create_content(self, user_client):
        blog_resp = user_client.post(
            reverse("blog-post-list-create"),
            {"title": "Nope", "slug": "nope", "content": "x", "status": "draft"},
            format="json",
        )
        docs_resp = user_client.post(
            reverse("docs-page-list-create"),
            {"title": "Nope", "slug": "nope-doc", "content": "x", "is_published": True},
            format="json",
        )
        assert blog_resp.status_code == status.HTTP_403_FORBIDDEN
        assert docs_resp.status_code == status.HTTP_403_FORBIDDEN
