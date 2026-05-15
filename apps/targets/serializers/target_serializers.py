"""Serializers for target management."""
from django.utils.crypto import get_random_string
from rest_framework import serializers

from apps.targets.models import Target


class TargetSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Target
        fields = [
            "id",
            "url",
            "is_active",
            "verification_method",
            "verification_token",
            "verification_status",
            "verified_at",
            "owner",
            "owner_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "verification_token",
            "verification_status",
            "verified_at",
            "owner_email",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data["verification_token"] = get_random_string(32)
        return super().create(validated_data)


class TargetVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)


class TargetOwnerAssignSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
