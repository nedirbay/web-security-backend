"""Serializers for admin panel features."""
from rest_framework import serializers

from apps.core.models import AuditLog, BlogPost, DocumentationPage, Role, SystemSetting
from apps.core.security import sanitize_text
from apps.targets.models import Target
from apps.users.models import CustomUser


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["created_at"]


class AdminUserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "role",
            "date_joined",
        ]


class AdminUserUpdateSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=False, min_value=1)
    is_active = serializers.BooleanField(required=False)


class AssignTargetSerializer(serializers.Serializer):
    target_id = serializers.IntegerField(min_value=1)


class SystemSettingSerializer(serializers.ModelSerializer):
    def validate_key(self, value):
        return sanitize_text(value)

    def validate_value(self, value):
        return sanitize_text(value)

    def validate_description(self, value):
        return sanitize_text(value)

    class Meta:
        model = SystemSetting
        fields = ["id", "key", "value", "description", "updated_by", "updated_at"]
        read_only_fields = ["updated_by", "updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_email", "action", "entity_type", "entity_id", "metadata", "created_at"]
        read_only_fields = ["created_at"]


class BlogPostSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "author",
            "author_email",
            "title",
            "slug",
            "content",
            "tags",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "author_email", "created_at", "updated_at"]


class DocumentationPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentationPage
        fields = ["id", "title", "slug", "category", "content", "is_published", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
