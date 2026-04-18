from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Notification


class CustomerRegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['name', 'email', 'phone', 'city', 'area', 'state',
                  'password', 'confirm_password']

    def validate_email(self, v):
        if User.objects.filter(email=v.lower()).exists():
            raise serializers.ValidationError('This email is already registered.')
        return v.lower()

    def validate_phone(self, v):
        digits = ''.join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise serializers.ValidationError('Please enter a valid 10-digit mobile number.')
        return v

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(role=User.CUSTOMER, **validated_data)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'name', 'email', 'phone', 'role',
                  'city', 'area', 'state', 'date_joined']
        read_only_fields = ['id', 'email', 'role', 'date_joined']


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Allows customer/provider to update name, phone, location."""
    class Meta:
        model  = User
        fields = ['name', 'phone', 'city', 'area', 'state']


class ChangePasswordSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'title', 'sub', 'type', 'is_read', 'created_at']
        read_only_fields = fields
