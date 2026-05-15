"""Views for scanner integration, scheduling, vulnerabilities and analytics."""
import os
import re

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scans.models import Scan, ScanSchedule, Vulnerability, ZapConfiguration
from apps.core.models import Notification
from apps.core.security import AdminIPWhitelistPermission
from apps.scans.serializers.scan_serializers import (
    ScanScheduleSerializer,
    ScanSerializer,
    VulnerabilitySerializer,
    ZapConfigurationSerializer,
)
from apps.scans.services.scheduler_service import enqueue_due_schedules, run_worker_once
from apps.scans.services.zap_client import ZapClient, parse_alerts


class APIScanRequestSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=["GET", "POST", "PUT", "PATCH", "DELETE"], default="GET")
    path = serializers.CharField(max_length=300)
    headers = serializers.DictField(required=False)
    body = serializers.DictField(required=False)


class JWTCheckSerializer(serializers.Serializer):
    token = serializers.CharField()


class GraphQLScanSerializer(serializers.Serializer):
    endpoint = serializers.URLField()
    query = serializers.CharField(required=False, allow_blank=True)


def _persist_vulnerabilities(scan: Scan):
    Vulnerability.objects.filter(scan=scan).delete()
    for alert in scan.parsed_alerts:
        Vulnerability.objects.create(
            scan=scan,
            target=scan.target,
            owner=scan.owner,
            name=alert.get("name", "Unknown"),
            severity=alert.get("risk", "Info"),
            owasp_category=alert.get("owasp", "Unknown"),
            url=alert.get("url", scan.target.url),
        )


def _create_scan_notification(scan: Scan):
    severity_rank = {"High": 3, "Medium": 2, "Low": 1, "Info": 0}
    highest = "Info"
    for alert in scan.parsed_alerts:
        risk = alert.get("risk", "Info")
        if severity_rank.get(risk, 0) > severity_rank.get(highest, 0):
            highest = risk
    Notification.objects.create(
        user=scan.owner,
        type=Notification.Type.INFO if scan.status == Scan.Status.COMPLETED else Notification.Type.WARNING,
        message=f"Scan #{scan.id} finished with status {scan.status}. Highest risk: {highest}.",
        is_read=False,
    )


def _execute_scan(scan: Scan):
    config = ZapConfiguration.objects.filter(owner=scan.owner, is_active=True).first()
    api_url = config.api_url if config else os.getenv("ZAP_API_URL", "http://localhost:8090")
    api_key = config.api_key if config else ""
    timeout = config.timeout_seconds if config else 120

    client = ZapClient(api_url=api_url, api_key=api_key, timeout_seconds=timeout)

    if scan.scan_type == Scan.ScanType.PASSIVE:
        started = client.spider_scan(scan.target.url, depth=scan.depth)
    elif scan.scan_type == Scan.ScanType.ACTIVE:
        started = client.active_scan(scan.target.url, attack_strength=scan.attack_strength)
    elif scan.scan_type == Scan.ScanType.API:
        started = client.api_scan(scan.target.url)
    else:
        started = client.spider_scan(scan.target.url, depth=scan.depth)
        client.active_scan(scan.target.url, attack_strength=scan.attack_strength)

    raw_results = client.get_alerts(scan.target.url)
    scan.zap_scan_id = started["scan_id"]
    scan.raw_results = raw_results
    scan.parsed_alerts = parse_alerts(raw_results)


class ScanListCreateView(generics.ListCreateAPIView):
    serializer_class = ScanSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Scan.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        target = serializer.validated_data["target"]
        if target.owner_id != self.request.user.id and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You cannot scan a target you do not own.")
        serializer.save(owner=self.request.user)


class ScanRunView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        scan = get_object_or_404(Scan, pk=pk, owner=request.user)
        scan.status = Scan.Status.RUNNING
        scan.save(update_fields=["status", "updated_at"])
        _execute_scan(scan)
        scan.status = Scan.Status.COMPLETED
        scan.save(update_fields=["status", "updated_at", "completed_at", "zap_scan_id", "raw_results", "parsed_alerts"])
        _persist_vulnerabilities(scan)
        _create_scan_notification(scan)
        return Response(ScanSerializer(scan).data, status=status.HTTP_200_OK)


class VulnerabilityListView(generics.ListAPIView):
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = Vulnerability.objects.filter(owner=self.request.user)
        severity = self.request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity__iexact=severity)
        return qs


class VulnerabilityGroupByOwaspView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = (
            Vulnerability.objects.filter(owner=request.user)
            .values("owasp_category")
            .annotate(count=Count("id"))
            .order_by("owasp_category")
        )
        return Response(list(data), status=status.HTTP_200_OK)


class VulnerabilityFalsePositiveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        vuln = get_object_or_404(Vulnerability, pk=pk, owner=request.user)
        vuln.is_false_positive = not vuln.is_false_positive
        vuln.save(update_fields=["is_false_positive", "updated_at"])
        return Response(VulnerabilitySerializer(vuln).data, status=status.HTTP_200_OK)


class VulnerabilityLifecycleUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        vuln = get_object_or_404(Vulnerability, pk=pk, owner=request.user)
        new_status = request.data.get("status")
        allowed = {"open", "reviewed", "fixed", "closed"}
        if new_status not in allowed:
            return Response({"detail": "Invalid lifecycle status."}, status=status.HTTP_400_BAD_REQUEST)
        vuln.lifecycle_status = new_status
        vuln.save(update_fields=["lifecycle_status", "updated_at"])
        return Response(VulnerabilitySerializer(vuln).data, status=status.HTTP_200_OK)


class ZapConfigurationListCreateView(generics.ListCreateAPIView):
    serializer_class = ZapConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ZapConfiguration.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ScanScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScanScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ScanSchedule.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        target = serializer.validated_data["target"]
        if target.owner_id != self.request.user.id and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You cannot schedule scans for this target.")
        serializer.save(owner=self.request.user)


class SchedulerEnqueueView(APIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]

    def post(self, request):
        count = enqueue_due_schedules()
        return Response({"enqueued": count}, status=status.HTTP_200_OK)


class SchedulerWorkerRunView(APIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]

    def post(self, request):
        processed = run_worker_once(_execute_scan)
        if processed is None:
            return Response({"processed": False}, status=status.HTTP_200_OK)
        _persist_vulnerabilities(processed)
        _create_scan_notification(processed)
        return Response({"processed": True, "scan_id": processed.id, "status": processed.status}, status=status.HTTP_200_OK)


class VulnerabilityTrendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = (
            Vulnerability.objects.filter(owner=request.user)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        return Response(list(data), status=status.HTTP_200_OK)


class MostCommonIssuesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = (
            Vulnerability.objects.filter(owner=request.user)
            .values("name")
            .annotate(count=Count("id"))
            .order_by("-count", "name")[:10]
        )
        return Response(list(data), status=status.HTTP_200_OK)


class ScanSuccessRateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scans = Scan.objects.filter(owner=request.user)
        total = scans.count()
        success = scans.filter(status=Scan.Status.COMPLETED).count()
        rate = (success / total * 100) if total else 0
        return Response({"total": total, "successful": success, "success_rate": round(rate, 2)}, status=status.HTTP_200_OK)


class RiskHeatmapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = (
            Vulnerability.objects.filter(owner=request.user)
            .values("target__url")
            .annotate(
                high=Count("id", filter=Q(severity="High")),
                medium=Count("id", filter=Q(severity="Medium")),
                low=Count("id", filter=Q(severity="Low")),
                info=Count("id", filter=Q(severity="Info")),
                total=Count("id"),
            )
            .order_by("target__url")
        )
        return Response(list(data), status=status.HTTP_200_OK)


class TimeBasedReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scans = Scan.objects.filter(owner=request.user)
        vulns = Vulnerability.objects.filter(owner=request.user)
        by_day = (
            vulns.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )
        return Response(
            {
                "scan_total": scans.count(),
                "scan_completed": scans.filter(status=Scan.Status.COMPLETED).count(),
                "scan_failed": scans.filter(status=Scan.Status.FAILED).count(),
                "vulnerability_total": vulns.count(),
                "vulnerabilities_by_day": list(by_day),
            },
            status=status.HTTP_200_OK,
        )


class APIScanSimulateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = APIScanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]
        path = serializer.validated_data["path"]
        headers = serializer.validated_data.get("headers", {})
        body = serializer.validated_data.get("body", {})

        findings = []
        if method in {"POST", "PUT", "PATCH"} and not body:
            findings.append({"name": "Empty request body", "severity": "Low"})
        if "Authorization" not in headers:
            findings.append({"name": "Missing Authorization header", "severity": "Medium"})
        if re.search(r"/admin|/internal", path, re.IGNORECASE):
            findings.append({"name": "Sensitive path exposure", "severity": "High"})

        return Response({"request": serializer.validated_data, "findings": findings}, status=status.HTTP_200_OK)


class JWTVulnerabilityCheckView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JWTCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]

        issues = []
        parts = token.split(".")
        if len(parts) != 3:
            issues.append("Malformed JWT format")
        if token.lower().startswith("bearer "):
            issues.append("Token should be raw JWT without Bearer prefix")
        if "none" in token.lower():
            issues.append("Potential none-alg usage indicator")
        return Response({"issues": issues, "risk": "High" if issues else "Low"}, status=status.HTTP_200_OK)


class GraphQLSecurityScanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GraphQLScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data.get("query", "")

        findings = []
        if "__schema" in query or "__type" in query:
            findings.append({"name": "Introspection query detected", "severity": "Medium"})
        if "mutation" in query and "auth" not in query.lower():
            findings.append({"name": "Mutation without visible auth context", "severity": "Low"})
        if not findings:
            findings.append({"name": "No obvious GraphQL anti-pattern found", "severity": "Info"})
        return Response({"endpoint": serializer.validated_data["endpoint"], "findings": findings}, status=status.HTTP_200_OK)


class HeaderAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        csp = request.META.get("HTTP_CSP", "")
        hsts = request.META.get("HTTP_STRICT_TRANSPORT_SECURITY", "")
        result = {
            "csp_present": bool(csp),
            "hsts_present": bool(hsts),
            "csp_status": "good" if csp else "missing",
            "hsts_status": "good" if hsts else "missing",
        }
        return Response(result, status=status.HTTP_200_OK)


class AIAssistantSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vulns = Vulnerability.objects.filter(owner=request.user, is_false_positive=False)
        high = vulns.filter(severity="High").count()
        medium = vulns.filter(severity="Medium").count()
        low = vulns.filter(severity="Low").count()
        risk = "Critical" if high >= 3 else "High" if high else "Medium" if medium else "Low"

        explanation = f"Detected {high} high, {medium} medium, {low} low vulnerabilities."
        suggestions = [
            "Prioritize patching high severity findings first.",
            "Enable strict security headers (CSP/HSTS) globally.",
            "Re-run active scans after fixes and close validated items.",
        ]
        return Response(
            {
                "risk_summary": risk,
                "vulnerability_explanation": explanation,
                "auto_fix_suggestions": suggestions,
            },
            status=status.HTTP_200_OK,
        )
