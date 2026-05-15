"""Lightweight OpenAPI-style schema endpoint for API discovery."""
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def _normalize_path(route: str) -> str:
    normalized = "/" + route.lstrip("/")
    normalized = normalized.replace("<int:", "{").replace("<str:", "{").replace("<slug:", "{")
    normalized = normalized.replace("<uuid:", "{").replace(">", "}")
    return normalized


def _collect_paths(patterns, prefix=""):
    paths = {}
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            child_prefix = prefix + str(pattern.pattern)
            paths.update(_collect_paths(pattern.url_patterns, child_prefix))
        elif isinstance(pattern, URLPattern):
            route = prefix + str(pattern.pattern)
            if route.startswith("admin/"):
                continue
            path = _normalize_path(route)
            paths[path] = {}
    return dict(sorted(paths.items()))


class OpenAPISchemaView(APIView):
    """Return a minimal OpenAPI-compatible document."""

    permission_classes = [AllowAny]

    def get(self, request):
        paths = _collect_paths(get_resolver().url_patterns)
        return Response(
            {
                "openapi": "3.0.0",
                "info": {"title": "Web Security Platform API", "version": "1.0.0"},
                "paths": paths,
            }
        )
