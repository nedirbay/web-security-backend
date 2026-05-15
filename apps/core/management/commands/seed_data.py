"""Seed initial data for local development/testing."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import BlogPost, DocumentationPage, Notification, Role, SystemSetting


class Command(BaseCommand):
    help = "Seed initial data (roles, admin, settings, sample content)."

    def handle(self, *args, **options):
        user_model = get_user_model()

        roles = {
            "admin": "Platform administrator",
            "user": "Regular user",
            "analyst": "Security analyst",
        }
        role_objs = {}
        for name, desc in roles.items():
            role, _ = Role.objects.get_or_create(name=name, defaults={"description": desc})
            role_objs[name] = role

        admin, _ = user_model.objects.get_or_create(
            email="seed-admin@example.com",
            defaults={
                "username": "seedadmin",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "role": role_objs["admin"],
            },
        )
        if not admin.has_usable_password():
            admin.set_password("AdminPass123!")
            admin.save(update_fields=["password"])

        user, _ = user_model.objects.get_or_create(
            email="seed-user@example.com",
            defaults={
                "username": "seeduser",
                "is_active": True,
                "role": role_objs["user"],
            },
        )

        SystemSetting.objects.get_or_create(
            key="maintenance_mode",
            defaults={"value": "off", "description": "Toggle maintenance mode", "updated_by": admin},
        )

        BlogPost.objects.get_or_create(
            slug="welcome-security-blog",
            defaults={
                "author": admin,
                "title": "Welcome to Security Blog",
                "content": "Initial seeded blog post.",
                "tags": "security,owasp",
                "status": BlogPost.Status.PUBLISHED,
                "published_at": timezone.now(),
            },
        )

        DocumentationPage.objects.get_or_create(
            slug="getting-started",
            defaults={
                "title": "Getting Started",
                "category": "guide",
                "content": "Initial documentation page.",
                "is_published": True,
            },
        )

        Notification.objects.get_or_create(
            user=user,
            message="Welcome to the platform.",
            defaults={"type": Notification.Type.INFO, "is_read": False},
        )

        self.stdout.write(self.style.SUCCESS("Seed data completed."))
