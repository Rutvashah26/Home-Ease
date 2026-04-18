"""
apps/admin_panel/views.py
All routes require IsAdminRole.
Mirrors the five sections of the admin sidebar:
  ov → overview/stats
  pr → approved providers
  cu → customers
  pe → pending providers
  bk → all bookings
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from apps.accounts.models import User, Notification
from apps.providers.models import ProviderProfile
from apps.bookings.models import Booking
from apps.accounts.serializers import UserProfileSerializer
from apps.providers.serializers import ProviderDetailSerializer
from apps.bookings.serializers import BookingSerializer
from .permissions import IsAdminRole


# ── Dashboard stats ────────────────────────────────────────────────────
# GET /api/v1/admin/stats/
@api_view(['GET'])
@permission_classes([IsAdminRole])
def stats(request):
    customers = User.objects.filter(role=User.CUSTOMER)
    providers = ProviderProfile.objects.filter(status=ProviderProfile.APPROVED)
    pending   = ProviderProfile.objects.filter(status=ProviderProfile.PENDING)
    bookings  = Booking.objects.all()

    # Recent 8 registrations (customers + pending providers merged, sorted by date)
    recent = []
    for c in customers.order_by('-date_joined')[:8]:
        recent.append({
            'name':   c.name,
            'type':   'Customer',
            'date':   c.date_joined.strftime('%d %b %Y'),
            'status': 'Active',
        })
    for p in pending.select_related('user').order_by('-applied_at')[:8]:
        recent.append({
            'name':   p.user.name,
            'type':   'Provider',
            'date':   p.applied_at.strftime('%d %b %Y'),
            'status': 'Pending',
        })
    recent.sort(key=lambda x: x['date'], reverse=True)

    return Response({
        'total_customers':   customers.count(),
        'total_providers':   providers.count(),
        'pending_providers': pending.count(),
        'total_bookings':    bookings.count(),
        'recent':            recent[:8],
    })


# ── List approved providers ────────────────────────────────────────────
# GET /api/v1/admin/providers/
@api_view(['GET'])
@permission_classes([IsAdminRole])
def list_providers(request):
    qs = ProviderProfile.objects.filter(
        status=ProviderProfile.APPROVED
    ).select_related('user').order_by('-approved_at')
    return Response(ProviderDetailSerializer(qs, many=True).data)


# ── List pending providers ─────────────────────────────────────────────
# GET /api/v1/admin/providers/pending/
@api_view(['GET'])
@permission_classes([IsAdminRole])
def list_pending(request):
    qs = ProviderProfile.objects.filter(
        status=ProviderProfile.PENDING
    ).select_related('user').order_by('applied_at')
    return Response(ProviderDetailSerializer(qs, many=True).data)


# ── Approve provider ───────────────────────────────────────────────────
# POST /api/v1/admin/providers/<id>/approve/
@api_view(['POST'])
@permission_classes([IsAdminRole])
def approve_provider(request, pk):
    try:
        profile = ProviderProfile.objects.select_related('user').get(pk=pk)
    except ProviderProfile.DoesNotExist:
        return Response({'error': 'Provider not found.'}, status=404)

    if profile.status != ProviderProfile.PENDING:
        return Response({'error': f'Provider is already {profile.status}.'}, status=400)

    profile.status      = ProviderProfile.APPROVED
    profile.approved_at = timezone.now()
    profile.is_available = True
    profile.save(update_fields=['status', 'approved_at', 'is_available'])

    Notification.objects.create(
        user=profile.user,
        title='🎉 Application Approved!',
        sub='Welcome to HomeEase! You can now log in and accept service requests.',
        type='green',
    )
    return Response({
        'message': f'{profile.user.name} has been approved.',
        'provider': ProviderDetailSerializer(profile).data,
    })


# ── Reject provider ────────────────────────────────────────────────────
# POST /api/v1/admin/providers/<id>/reject/
@api_view(['POST'])
@permission_classes([IsAdminRole])
def reject_provider(request, pk):
    try:
        profile = ProviderProfile.objects.select_related('user').get(pk=pk)
    except ProviderProfile.DoesNotExist:
        return Response({'error': 'Provider not found.'}, status=404)

    if profile.status != ProviderProfile.PENDING:
        return Response({'error': f'Provider is already {profile.status}.'}, status=400)

    profile.status = ProviderProfile.REJECTED
    profile.save(update_fields=['status'])
    return Response({'message': f'{profile.user.name} application has been rejected.'})


# ── List all customers ─────────────────────────────────────────────────
# GET /api/v1/admin/customers/
@api_view(['GET'])
@permission_classes([IsAdminRole])
def list_customers(request):
    qs = User.objects.filter(role=User.CUSTOMER).order_by('-date_joined')
    return Response(UserProfileSerializer(qs, many=True).data)


# ── Toggle user active/inactive ────────────────────────────────────────
# POST /api/v1/admin/users/<id>/toggle/
@api_view(['POST'])
@permission_classes([IsAdminRole])
def toggle_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    if user.is_admin_role:
        return Response({'error': 'Cannot deactivate admin accounts.'}, status=400)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    action = 'activated' if user.is_active else 'deactivated'
    return Response({'message': f'{user.name} has been {action}.', 'is_active': user.is_active})


# ── All bookings ───────────────────────────────────────────────────────
# GET /api/v1/admin/bookings/?status=
@api_view(['GET'])
@permission_classes([IsAdminRole])
def list_bookings(request):
    qs = Booking.objects.select_related(
        'customer', 'provider_profile__user'
    ).order_by('-created_at')
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response(BookingSerializer(qs, many=True).data)
