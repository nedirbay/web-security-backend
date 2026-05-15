"""Serializers for scan workflows."""
from rest_framework import serializers

from apps.scans.models import Scan, ScanSchedule, Vulnerability, ZapConfiguration


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = [
            "id",
            "owner",
            "target",
            "scan_type",
            "status",
            "depth",
            "attack_strength",
            "use_context",
            "proxy_enabled",
            "proxy_host",
            "proxy_port",
            "queue_backend",
            "retry_count",
            "max_retries",
            "zap_scan_id",
            "raw_results",
            "parsed_alerts",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = [
            "owner",
            "status",
            "retry_count",
            "zap_scan_id",
            "raw_results",
            "parsed_alerts",
            "created_at",
            "updated_at",
            "completed_at",
        ]


class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            "id",
            "scan",
            "target",
            "owner",
            "name",
            "severity",
            "owasp_category",
            "url",
            "is_false_positive",
            "lifecycle_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at", "scan", "target"]


class ZapConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZapConfiguration
        fields = ["id", "owner", "api_url", "api_key", "timeout_seconds", "is_active", "created_at"]
        read_only_fields = ["owner", "created_at"]


class ScanScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanSchedule
        fields = [
            "id",
            "owner",
            "target",
            "scan_type",
            "frequency",
            "custom_interval_minutes",
            "next_run_at",
            "is_enabled",
            "queue_backend",
            "max_retries",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]
