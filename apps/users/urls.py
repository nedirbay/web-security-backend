"""
URLs for user management.
"""
from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserListView,
    UserDetailView,
    UserProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserLogoutView,
    APIKeyListCreateView,
    APIKeyDetailView,
)

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    
    # Users
    path('', UserListView.as_view(), name='user-list'),
    path('me/', UserDetailView.as_view(), name='user-me'),
    
    # Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Password Reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # API Keys
    path('api-keys/', APIKeyListCreateView.as_view(), name='api-key-list-create'),
    path('api-keys/<int:pk>/', APIKeyDetailView.as_view(), name='api-key-detail'),
]
