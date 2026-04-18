"""
apps/bookings/serializers.py
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Booking


class BookingCreateSerializer(serializers.Serializer):
    provider_profile_id = serializers.IntegerField()
    description         = serializers.CharField()
    date                = serializers.DateField()
    time                = serializers.CharField(max_length=10)
    customer_address    = serializers.CharField()

    def validate_date(self, v):
        if v < timezone.localdate():
            raise serializers.ValidationError('Date cannot be in the past.')
        return v


class BookingSerializer(serializers.ModelSerializer):
    """Full booking representation returned to both customer and provider."""
    has_review = serializers.SerializerMethodField()

    class Meta:
        model  = Booking
        fields = [
            'id',
            'customer_name', 'customer_phone', 'customer_email', 'customer_address',
            'provider_name', 'provider_skill', 'provider_phone',
            'description', 'date', 'time',
            'status', 'created_at', 'updated_at', 'completed_at',
            'has_review',
            # FK ids for re-fetching
            'provider_profile',
        ]
        read_only_fields = fields

    def get_has_review(self, obj):
        return hasattr(obj, 'review')
