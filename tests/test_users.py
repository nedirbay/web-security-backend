"""
Tests for user management functionality.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email='admin@example.com',
        username='admin',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    # Get JWT token
    response = api_client.post(
        reverse('user-login'),
        {'email': 'test@example.com', 'password': 'testpass123'},
        format='json'
    )
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration."""
    
    def test_register_new_user(self, api_client):
        """Test registering a new user."""
        url = reverse('user-register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'email' in response.data
        assert 'username' in response.data
        assert User.objects.filter(email='newuser@example.com').exists()
    
    def test_register_with_mismatched_passwords(self, api_client):
        """Test registration with mismatched passwords."""
        url = reverse('user-register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password_confirm': 'DifferentPass123!',
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data
    
    def test_register_with_weak_password(self, api_client):
        """Test registration with weak password."""
        url = reverse('user-register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'weak',
            'password_confirm': 'weak',
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_register_with_existing_email(self, api_client, test_user):
        """Test registration with existing email."""
        url = reverse('user-register')
        data = {
            'email': 'test@example.com',
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Test user login."""
    
    def test_login_with_valid_credentials(self, api_client, test_user):
        """Test login with valid credentials."""
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_with_invalid_credentials(self, api_client, test_user):
        """Test login with invalid credentials."""
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_with_nonexistent_user(self, api_client):
        """Test login with nonexistent user."""
        url = reverse('user-login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile management."""
    
    def test_get_profile(self, authenticated_client, test_user):
        """Test getting user profile."""
        url = reverse('user-profile')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
    
    def test_update_profile(self, authenticated_client, test_user):
        """Test updating user profile."""
        url = reverse('user-profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Test bio',
            'website': 'https://example.com'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        assert test_user.first_name == 'Updated'
        assert test_user.last_name == 'Name'


@pytest.mark.django_db
class TestUserDetails:
    """Test user details endpoint."""
    
    def test_get_user_details(self, authenticated_client, test_user):
        """Test getting current user details."""
        url = reverse('user-me')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
        assert response.data['username'] == 'testuser'


@pytest.mark.django_db
class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_password_reset_request(self, api_client, test_user):
        """Test password reset request."""
        url = reverse('password-reset')
        data = {'email': 'test@example.com'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
    
    def test_password_reset_confirm(self, api_client):
        """Test password reset confirmation."""
        url = reverse('password-reset-confirm')
        data = {
            'token': 'test-token',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
    
    def test_password_reset_confirm_with_mismatch(self, api_client):
        """Test password reset confirmation with mismatched passwords."""
        url = reverse('password-reset-confirm')
        data = {
            'token': 'test-token',
            'password': 'NewPass123!',
            'password_confirm': 'Different123!'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data


@pytest.mark.django_db
class TestAPIKeyManagement:
    """Test API key management."""
    
    def test_create_api_key(self, authenticated_client, test_user):
        """Test creating an API key."""
        url = reverse('api-key-list-create')
        data = {'name': 'Test API Key'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'key' in response.data
        assert response.data['name'] == 'Test API Key'
        assert len(response.data['key']) == 64
    
    def test_list_api_keys(self, authenticated_client, test_user):
        """Test listing API keys."""
        url = reverse('api-key-list-create')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_get_api_key_detail(self, authenticated_client, test_user):
        """Test getting API key detail."""
        # Create an API key first
        create_url = reverse('api-key-list-create')
        create_data = {'name': 'Test API Key'}
        create_response = authenticated_client.post(create_url, create_data, format='json')
        api_key_id = create_response.data['id']
        
        # Get the detail
        detail_url = reverse('api-key-detail', kwargs={'pk': api_key_id})
        response = authenticated_client.get(detail_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == api_key_id
        assert response.data['name'] == 'Test API Key'
    
    def test_delete_api_key(self, authenticated_client, test_user):
        """Test deleting an API key."""
        # Create an API key first
        create_url = reverse('api-key-list-create')
        create_data = {'name': 'Test API Key to Delete'}
        create_response = authenticated_client.post(create_url, create_data, format='json')
        api_key_id = create_response.data['id']
        
        # Delete the key
        detail_url = reverse('api-key-detail', kwargs={'pk': api_key_id})
        response = authenticated_client.delete(detail_url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deactivated (not actually deleted)
        from apps.users.models import APIKey
        api_key = APIKey.objects.get(id=api_key_id)
        assert api_key.is_active == False
