"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/admin/', include('apps.core.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/targets/', include('apps.targets.urls')),
    path('api/scans/', include('apps.scans.urls')),
]
