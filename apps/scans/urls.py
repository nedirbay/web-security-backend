"""URLs for scanner integration."""
from django.urls import path

from .views import (
    MostCommonIssuesView,
    RiskHeatmapView,
    ScanListCreateView,
    ScanRunView,
    ScanScheduleListCreateView,
    ScanSuccessRateView,
    SchedulerEnqueueView,
    SchedulerWorkerRunView,
    TimeBasedReportView,
    VulnerabilityTrendView,
    VulnerabilityFalsePositiveView,
    VulnerabilityGroupByOwaspView,
    VulnerabilityLifecycleUpdateView,
    VulnerabilityListView,
    ZapConfigurationListCreateView,
)

urlpatterns = [
    path("", ScanListCreateView.as_view(), name="scan-list-create"),
    path("<int:pk>/run/", ScanRunView.as_view(), name="scan-run"),
    path("config/zap/", ZapConfigurationListCreateView.as_view(), name="zap-config-list-create"),
    path("schedules/", ScanScheduleListCreateView.as_view(), name="scan-schedule-list-create"),
    path("scheduler/enqueue/", SchedulerEnqueueView.as_view(), name="scan-scheduler-enqueue"),
    path("scheduler/worker-run/", SchedulerWorkerRunView.as_view(), name="scan-scheduler-worker-run"),
    path("vulnerabilities/", VulnerabilityListView.as_view(), name="vulnerability-list"),
    path("vulnerabilities/group-by-owasp/", VulnerabilityGroupByOwaspView.as_view(), name="vulnerability-group-owasp"),
    path("vulnerabilities/<int:pk>/false-positive/", VulnerabilityFalsePositiveView.as_view(), name="vulnerability-false-positive"),
    path("vulnerabilities/<int:pk>/lifecycle/", VulnerabilityLifecycleUpdateView.as_view(), name="vulnerability-lifecycle"),
    path("analytics/vulnerability-trends/", VulnerabilityTrendView.as_view(), name="analytics-vulnerability-trends"),
    path("analytics/common-issues/", MostCommonIssuesView.as_view(), name="analytics-common-issues"),
    path("analytics/scan-success-rate/", ScanSuccessRateView.as_view(), name="analytics-scan-success-rate"),
    path("analytics/risk-heatmap/", RiskHeatmapView.as_view(), name="analytics-risk-heatmap"),
    path("analytics/time-based-report/", TimeBasedReportView.as_view(), name="analytics-time-based-report"),
]
