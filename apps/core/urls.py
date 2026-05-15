"""Admin panel URLs."""
from django.urls import path

from apps.core.views import (
    AdminAssignTargetView,
    AdminDashboardView,
    AdminUserListView,
    AdminUserManageView,
    AuditLogListView,
    BlogPostDetailView,
    BlogPostListCreateView,
    DocumentationPageDetailView,
    DocumentationPageListCreateView,
    RoleListView,
    SystemSettingDetailView,
    SystemSettingListCreateView,
)

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:pk>/", AdminUserManageView.as_view(), name="admin-user-manage"),
    path("users/<int:pk>/assign-target/", AdminAssignTargetView.as_view(), name="admin-assign-target"),
    path("roles/", RoleListView.as_view(), name="admin-role-list"),
    path("settings/", SystemSettingListCreateView.as_view(), name="admin-setting-list-create"),
    path("settings/<int:pk>/", SystemSettingDetailView.as_view(), name="admin-setting-detail"),
    path("audit-logs/", AuditLogListView.as_view(), name="admin-audit-log-list"),
    path("blog-posts/", BlogPostListCreateView.as_view(), name="blog-post-list-create"),
    path("blog-posts/<int:pk>/", BlogPostDetailView.as_view(), name="blog-post-detail"),
    path("docs-pages/", DocumentationPageListCreateView.as_view(), name="docs-page-list-create"),
    path("docs-pages/<int:pk>/", DocumentationPageDetailView.as_view(), name="docs-page-detail"),
]
