"""
apps/accounts/views.py
Endpoints: register customer, login (all roles), logout,
           profile CRUD, change password, notifications.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User, Notification
from .serializers import (
    CustomerRegisterSerializer, LoginSerializer,
    UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, NotificationSerializer,
)


def _tokens(user):
    r = RefreshToken.for_user(user)
    return {'refresh': str(r), 'access': str(r.access_token)}


# ── Register customer ─────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register_customer(request):
    s = CustomerRegisterSerializer(data=request.data)
    if s.is_valid():
        user = s.save()
        # welcome notification
        Notification.objects.create(
            user=user, title='Welcome to HomeEase! 🎉',
            sub='Your account was created successfully.', type='green'
        )
        return Response({'message': 'Account created.',
                         'user': UserProfileSerializer(user).data,
                         **_tokens(user)}, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Login (customer / provider / admin) ───────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    s = LoginSerializer(data=request.data)
    s.is_valid(raise_exception=True)

    user = authenticate(request,
                        username=s.validated_data['email'].lower(),
                        password=s.validated_data['password'])
    if user is None:
        return Response({'error': 'No account found with these credentials.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({'error': 'Your account has been deactivated.'},
                        status=status.HTTP_403_FORBIDDEN)

    # Providers must be approved
    if user.is_provider:
        try:
            profile = user.provider_profile
            if profile.status == 'pending':
                return Response(
                    {'error': 'Your application is still pending admin approval.',
                     'status': 'pending'},
                    status=status.HTTP_403_FORBIDDEN)
            if profile.status == 'rejected':
                return Response(
                    {'error': 'Your application was rejected. Contact support.',
                     'status': 'rejected'},
                    status=status.HTTP_403_FORBIDDEN)
        except Exception:
            pass

    return Response({'message': 'Login successful.',
                     'user': UserProfileSerializer(user).data,
                     **_tokens(user)})


# ── Logout (blacklist refresh token) ─────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        RefreshToken(request.data['refresh']).blacklist()
        return Response({'message': 'Logged out.'})
    except Exception:
        return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Profile — view & update ───────────────────────────────────────────
class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateProfileSerializer
        return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        s = UpdateProfileSerializer(instance, data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(UserProfileSerializer(instance).data)


# ── Change password ───────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    s = ChangePasswordSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    if not request.user.check_password(s.validated_data['old_password']):
        return Response({'error': 'Current password is incorrect.'},
                        status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(s.validated_data['new_password'])
    request.user.save()
    return Response({'message': 'Password updated successfully.'})


# ── Notifications ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    notifs = Notification.objects.filter(user=request.user)[:30]
    return Response(NotificationSerializer(notifs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All notifications marked as read.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread': count})
