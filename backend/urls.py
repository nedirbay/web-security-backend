"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from .api_docs import OpenAPISchemaView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', OpenAPISchemaView.as_view(), name='openapi-schema'),
    path(
        'api/docs/',
        TemplateView.as_view(template_name='swagger_ui.html', extra_context={'schema_url_name': 'openapi-schema'}),
        name='swagger-ui',
    ),
    path('api/admin/', include('apps.core.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/targets/', include('apps.targets.urls')),
    path('api/scans/', include('apps.scans.urls')),
]
