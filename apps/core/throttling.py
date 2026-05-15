"""Custom throttling classes for API layer."""
from rest_framework.throttling import UserRateThrottle


class UserRateThrottleWithAdminBypass(UserRateThrottle):
    """Apply user rate limits except for admin/staff users."""

    def allow_request(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and (user.is_superuser or user.is_staff):
            return True
        return super().allow_request(request, view)
