"""URLs for target management."""
from django.urls import path

from .views import (
    TargetAssignOwnerView,
    TargetDetailView,
    TargetListCreateView,
    TargetToggleActiveView,
    TargetVerifyOwnershipView,
)

urlpatterns = [
    path("", TargetListCreateView.as_view(), name="target-list-create"),
    path("<int:pk>/", TargetDetailView.as_view(), name="target-detail"),
    path("<int:pk>/toggle-active/", TargetToggleActiveView.as_view(), name="target-toggle-active"),
    path("<int:pk>/verify-ownership/", TargetVerifyOwnershipView.as_view(), name="target-verify-ownership"),
    path("<int:pk>/assign-owner/", TargetAssignOwnerView.as_view(), name="target-assign-owner"),
]
