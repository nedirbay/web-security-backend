"""Security helpers: admin IP filtering and input sanitization."""
import ipaddress
import os

from django.utils.html import strip_tags
from rest_framework.permissions import BasePermission


def sanitize_text(value: str) -> str:
    if value is None:
        return value
    return strip_tags(value).strip()


class AdminIPWhitelistPermission(BasePermission):
    """Allow admin endpoints only for trusted client IPs."""

    message = "Admin access is restricted for this IP address."

    def has_permission(self, request, view):
        raw = os.getenv("ADMIN_IP_WHITELIST", "127.0.0.1,::1,localhost")
        allowed = {item.strip() for item in raw.split(",") if item.strip()}
        client_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
            "REMOTE_ADDR", ""
        )
        if not client_ip:
            return False

        # allow direct literal match first (incl. localhost)
        if client_ip in allowed:
            return True

        try:
            ip = ipaddress.ip_address(client_ip)
        except ValueError:
            return False

        for entry in allowed:
            try:
                if "/" in entry:
                    if ip in ipaddress.ip_network(entry, strict=False):
                        return True
                elif ip == ipaddress.ip_address(entry):
                    return True
            except ValueError:
                continue
        return False
