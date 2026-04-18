"""
apps/bookings/models.py

Status lifecycle (mirrors frontend exactly):
  pending → accepted  → completed
  pending → declined
  pending → cancelled  (by customer)
  accepted → cancelled (by customer)
"""
from django.db import models
from django.conf import settings


class Booking(models.Model):
    PENDING   = 'pending'
    ACCEPTED  = 'accepted'
    COMPLETED = 'completed'
    DECLINED  = 'declined'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING,   'Pending'),
        (ACCEPTED,  'Accepted'),
        (COMPLETED, 'Completed'),
        (DECLINED,  'Declined'),
        (CANCELLED, 'Cancelled'),
    ]

    # Parties
    customer         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bookings_as_customer')
    provider_profile = models.ForeignKey(
        'providers.ProviderProfile', on_delete=models.CASCADE,
        related_name='bookings')

    # Denormalised snapshot (matches frontend fields exactly)
    # These are stored at booking time so records survive profile edits.
    customer_name    = models.CharField(max_length=120)
    customer_phone   = models.CharField(max_length=20, blank=True)
    customer_email   = models.EmailField(blank=True)
    customer_address = models.TextField()          # service location
    provider_name    = models.CharField(max_length=120)
    provider_skill   = models.CharField(max_length=80)
    provider_phone   = models.CharField(max_length=20, blank=True)

    # Request details
    description = models.TextField()              # what the customer needs
    date        = models.DateField()              # requested date
    time        = models.CharField(max_length=10) # e.g. "10:30"

    # State
    status       = models.CharField(max_length=12, choices=STATUS_CHOICES,
                                    default=PENDING, db_index=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'he_bookings'
        ordering = ['-created_at']

    def __str__(self):
        return (f'Booking #{self.pk} — {self.customer_name} → '
                f'{self.provider_name} [{self.status}]')

    # helpers used by views
    @property
    def is_active(self):
        return self.status in (self.PENDING, self.ACCEPTED)

    @property
    def is_history(self):
        return self.status in (self.COMPLETED, self.CANCELLED, self.DECLINED)
