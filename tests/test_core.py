"""
Tests for the core app configuration and setup.
"""
import pytest
from django.apps import apps
from django.conf import settings


@pytest.mark.django_db
class TestCoreSetup:
    """Test core Django and DRF setup."""
    
    def test_installed_apps(self):
        """Test that all required apps are installed."""
        required_apps = [
            'apps.core',
            'apps.users',
            'apps.scans',
            'apps.targets',
            'rest_framework',
            'rest_framework_simplejwt',
            'corsheaders',
        ]
        for app in required_apps:
            assert app in settings.INSTALLED_APPS, f"{app} not in INSTALLED_APPS"
    
    def test_custom_user_model(self):
        """Test that custom user model is configured."""
        assert settings.AUTH_USER_MODEL == 'users.CustomUser'
    
    def test_rest_framework_config(self):
        """Test DRF configuration."""
        assert 'rest_framework' in settings.INSTALLED_APPS
        assert 'DEFAULT_AUTHENTICATION_CLASSES' in settings.REST_FRAMEWORK
        assert 'DEFAULT_PERMISSION_CLASSES' in settings.REST_FRAMEWORK
        assert 'EXCEPTION_HANDLER' in settings.REST_FRAMEWORK
    
    def test_jwt_settings(self):
        """Test JWT settings are configured."""
        assert hasattr(settings, 'SIMPLE_JWT')
        assert 'ACCESS_TOKEN_LIFETIME' in settings.SIMPLE_JWT
        assert 'REFRESH_TOKEN_LIFETIME' in settings.SIMPLE_JWT
    
    def test_cors_settings(self):
        """Test CORS settings are configured."""
        assert hasattr(settings, 'CORS_ALLOWED_ORIGINS')
        assert hasattr(settings, 'CORS_ALLOW_CREDENTIALS')
    
    def test_core_app_config(self):
        """Test core app configuration."""
        core_config = apps.get_app_config('core')
        assert core_config.name == 'apps.core'
        assert core_config.verbose_name == 'Core'
    
    def test_users_app_config(self):
        """Test users app configuration."""
        users_config = apps.get_app_config('users')
        assert users_config.name == 'apps.users'
        assert users_config.verbose_name == 'Users'
    
    def test_scans_app_config(self):
        """Test scans app configuration."""
        scans_config = apps.get_app_config('scans')
        assert scans_config.name == 'apps.scans'
        assert scans_config.verbose_name == 'Scans'
    
    def test_targets_app_config(self):
        """Test targets app configuration."""
        targets_config = apps.get_app_config('targets')
        assert targets_config.name == 'apps.targets'
        assert targets_config.verbose_name == 'Targets'


@pytest.mark.django_db
class TestCustomExceptionHandler:
    """Test custom exception handler."""
    
    def test_exception_handler_import(self):
        """Test that custom exception handler can be imported."""
        from apps.core.exceptions import custom_exception_handler, CustomValidationError
        assert callable(custom_exception_handler)
        assert issubclass(CustomValidationError, Exception)
