"""Database layer tests: models, migrations readiness, seed data."""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.core.models import BlogPost, DocumentationPage, Notification, Role, SystemSetting

User = get_user_model()


@pytest.mark.django_db
class TestDatabaseModels:
    def test_required_tables_models_exist(self):
        assert Role.objects.count() == 0
        assert SystemSetting.objects.count() == 0
        assert Notification.objects.count() == 0
        assert BlogPost.objects.count() == 0
        assert DocumentationPage.objects.count() == 0

    def test_model_relationships_and_constraints(self):
        admin_role = Role.objects.create(name="admin", description="Admin")
        user = User.objects.create_user(email="db-user@example.com", username="dbuser", password="pass12345", role=admin_role)

        SystemSetting.objects.create(key="test_key", value="1", updated_by=user)
        Notification.objects.create(user=user, type="info", message="hello")
        BlogPost.objects.create(author=user, title="T", slug="t-1", content="C")
        DocumentationPage.objects.create(title="D", slug="d-1", content="Doc")

        assert user.role.name == "admin"
        assert user.notifications.count() == 1
        assert user.blog_posts.count() == 1


@pytest.mark.django_db
class TestSeedData:
    def test_seed_command_populates_core_data(self):
        call_command("seed_data")

        assert Role.objects.filter(name="admin").exists()
        assert Role.objects.filter(name="user").exists()
        assert Role.objects.filter(name="analyst").exists()
        assert User.objects.filter(email="seed-admin@example.com").exists()
        assert SystemSetting.objects.filter(key="maintenance_mode").exists()
        assert BlogPost.objects.filter(slug="welcome-security-blog").exists()
        assert DocumentationPage.objects.filter(slug="getting-started").exists()
        assert Notification.objects.filter(message="Welcome to the platform.").exists()

    def test_seed_command_is_idempotent(self):
        call_command("seed_data")
        call_command("seed_data")

        assert Role.objects.filter(name="admin").count() == 1
        assert User.objects.filter(email="seed-admin@example.com").count() == 1
        assert SystemSetting.objects.filter(key="maintenance_mode").count() == 1
        assert BlogPost.objects.filter(slug="welcome-security-blog").count() == 1
        assert DocumentationPage.objects.filter(slug="getting-started").count() == 1
