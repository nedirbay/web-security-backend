"""
Serializers for user management.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.security import sanitize_text
from apps.users.models import CustomUser, UserProfile, APIKey


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _("Passwords do not match.")
            })
        
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class UserLoginSerializer(TokenObtainPairSerializer):
    """Serializer for user login with JWT."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    
    class Meta:
        model = UserProfile
        fields = (
            'email', 'username', 'first_name', 'last_name',
            'avatar', 'bio', 'website',
        )
        read_only_fields = ('email', 'username')
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                if isinstance(value, str):
                    value = sanitize_text(value)
                setattr(user, attr, value)
            user.save()
        if "bio" in validated_data and isinstance(validated_data["bio"], str):
            validated_data["bio"] = sanitize_text(validated_data["bio"])
        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user basic information."""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_active', 'is_staff', 'date_joined', 'profile'
        )
        read_only_fields = ('id', 'is_active', 'is_staff', 'date_joined')


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _("Passwords do not match.")
            })
        return attrs


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API key management."""
    key = serializers.CharField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = ('id', 'key', 'name', 'created_at', 'is_active', 'last_used_at')
        read_only_fields = ('id', 'key', 'created_at', 'last_used_at')
