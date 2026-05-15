"""Serializers for admin panel features."""
from rest_framework import serializers

from apps.core.models import AuditLog, Role, SystemSetting
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
