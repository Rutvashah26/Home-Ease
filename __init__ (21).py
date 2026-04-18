"""
apps/bookings/views.py

Booking status state-machine:
  Customer:  pending  → cancelled
             accepted → cancelled
  Provider:  pending  → accepted | declined
             accepted → completed
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from apps.accounts.models import Notification
from apps.providers.models import ProviderProfile
from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer


def _notify(user, title, sub, ntype='green'):
    Notification.objects.create(user=user, title=title, sub=sub, type=ntype)


def _fmt_date(d):
    """e.g. '05 Apr 2026'"""
    return d.strftime('%d %b %Y') if d else ''


# ── Create booking (customer only) ────────────────────────────────────
# POST /api/v1/bookings/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    if not request.user.is_customer:
        return Response({'error': 'Only customers can create bookings.'}, status=403)

    s = BookingCreateSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data

    try:
        profile = ProviderProfile.objects.select_related('user').get(
            pk=d['provider_profile_id'], status=ProviderProfile.APPROVED)
    except ProviderProfile.DoesNotExist:
        return Response({'error': 'Provider not found.'}, status=404)

    u = request.user
    booking = Booking.objects.create(
        customer=u,
        provider_profile=profile,
        customer_name=u.name,
        customer_phone=u.phone,
        customer_email=u.email,
        customer_address=d['customer_address'],
        provider_name=profile.user.name,
        provider_skill=profile.skill,
        provider_phone=profile.user.phone,
        description=d['description'],
        date=d['date'],
        time=d['time'],
    )

    date_str = _fmt_date(booking.date)

    # Notify provider
    _notify(profile.user,
            '📋 New Booking Request!',
            f'{u.name} has requested {profile.skill} on {date_str} at {booking.time}',
            'orange')

    # Notify customer
    _notify(u,
            '✅ Booking Submitted!',
            f'Your request to {profile.user.name} for {profile.skill} is pending confirmation.',
            'green')

    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


# ── My bookings — customer ────────────────────────────────────────────
# GET /api/v1/bookings/mine/?tab=active|history
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    if not request.user.is_customer:
        return Response({'error': 'Customers only.'}, status=403)

    tab = request.query_params.get('tab', 'active')
    qs  = Booking.objects.filter(customer=request.user).prefetch_related('review')

    if tab == 'history':
        qs = qs.filter(status__in=[Booking.COMPLETED, Booking.CANCELLED, Booking.DECLINED])
    else:
        qs = qs.filter(status__in=[Booking.PENDING, Booking.ACCEPTED])

    return Response(BookingSerializer(qs, many=True).data)


# ── My requests — provider ────────────────────────────────────────────
# GET /api/v1/bookings/requests/?tab=active|history
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def provider_requests(request):
    if not request.user.is_provider:
        return Response({'error': 'Providers only.'}, status=403)

    tab = request.query_params.get('tab', 'active')
    qs  = Booking.objects.filter(
        provider_profile=request.user.provider_profile
    ).prefetch_related('review')

    if tab == 'history':
        qs = qs.filter(status__in=[Booking.COMPLETED, Booking.CANCELLED, Booking.DECLINED])
    else:
        qs = qs.filter(status__in=[Booking.PENDING, Booking.ACCEPTED])

    return Response(BookingSerializer(qs, many=True).data)


# ── Provider stats ────────────────────────────────────────────────────
# GET /api/v1/bookings/provider-stats/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def provider_stats(request):
    if not request.user.is_provider:
        return Response({'error': 'Providers only.'}, status=403)
    qs = Booking.objects.filter(provider_profile=request.user.provider_profile)
    return Response({
        'pending':   qs.filter(status=Booking.PENDING).count(),
        'accepted':  qs.filter(status=Booking.ACCEPTED).count(),
        'completed': qs.filter(status=Booking.COMPLETED).count(),
    })


# ── Single booking detail ─────────────────────────────────────────────
# GET /api/v1/bookings/<id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, pk):
    try:
        bk = Booking.objects.prefetch_related('review').get(pk=pk)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    u = request.user
    owns = (
        (u.is_customer and bk.customer == u) or
        (u.is_provider and bk.provider_profile == u.provider_profile) or
        u.is_admin_role
    )
    if not owns:
        return Response({'error': 'Access denied.'}, status=403)
    return Response(BookingSerializer(bk).data)


# ── Cancel booking (customer) ─────────────────────────────────────────
# POST /api/v1/bookings/<id>/cancel/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, pk):
    if not request.user.is_customer:
        return Response({'error': 'Customers only.'}, status=403)
    try:
        bk = Booking.objects.get(pk=pk, customer=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    if bk.status not in (Booking.PENDING, Booking.ACCEPTED):
        return Response({'error': f'Cannot cancel a {bk.status} booking.'}, status=400)

    bk.status = Booking.CANCELLED
    bk.save(update_fields=['status', 'updated_at'])

    _notify(bk.provider_profile.user,
            '❌ Booking Cancelled',
            f'{bk.customer_name} cancelled the {bk.provider_skill} booking for {_fmt_date(bk.date)}',
            'red')

    return Response(BookingSerializer(bk).data)


# ── Accept booking (provider) ─────────────────────────────────────────
# POST /api/v1/bookings/<id>/accept/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_booking(request, pk):
    if not request.user.is_provider:
        return Response({'error': 'Providers only.'}, status=403)
    try:
        bk = Booking.objects.get(pk=pk, provider_profile=request.user.provider_profile)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    if bk.status != Booking.PENDING:
        return Response({'error': f'Cannot accept a {bk.status} booking.'}, status=400)

    bk.status = Booking.ACCEPTED
    bk.save(update_fields=['status', 'updated_at'])

    _notify(bk.customer,
            '✅ Booking Confirmed!',
            f'{bk.provider_name} has accepted your request for {bk.provider_skill} '
            f'on {_fmt_date(bk.date)} at {bk.time}',
            'green')

    return Response(BookingSerializer(bk).data)


# ── Decline booking (provider) ────────────────────────────────────────
# POST /api/v1/bookings/<id>/decline/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_booking(request, pk):
    if not request.user.is_provider:
        return Response({'error': 'Providers only.'}, status=403)
    try:
        bk = Booking.objects.get(pk=pk, provider_profile=request.user.provider_profile)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    if bk.status != Booking.PENDING:
        return Response({'error': f'Cannot decline a {bk.status} booking.'}, status=400)

    bk.status = Booking.DECLINED
    bk.save(update_fields=['status', 'updated_at'])

    _notify(bk.customer,
            '⚠️ Booking Not Available',
            f'{bk.provider_name} could not accept your request for {_fmt_date(bk.date)}. '
            'Please try booking another provider.',
            'orange')

    return Response(BookingSerializer(bk).data)


# ── Mark complete (provider) ──────────────────────────────────────────
# POST /api/v1/bookings/<id>/complete/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_booking(request, pk):
    if not request.user.is_provider:
        return Response({'error': 'Providers only.'}, status=403)
    try:
        bk = Booking.objects.get(pk=pk, provider_profile=request.user.provider_profile)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    if bk.status != Booking.ACCEPTED:
        return Response({'error': f'Cannot complete a {bk.status} booking.'}, status=400)

    bk.status       = Booking.COMPLETED
    bk.completed_at = timezone.now()
    bk.save(update_fields=['status', 'completed_at', 'updated_at'])

    _notify(bk.customer,
            '🏆 Service Completed!',
            f'Your {bk.provider_skill} service by {bk.provider_name} is complete. '
            'Please leave a review!',
            'green')

    return Response(BookingSerializer(bk).data)
