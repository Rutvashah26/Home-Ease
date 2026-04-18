from django.urls import path
from . import views

urlpatterns = [
    path('stats/',                       views.stats,             name='admin-stats'),
    path('providers/',                   views.list_providers,    name='admin-providers'),
    path('providers/pending/',           views.list_pending,      name='admin-pending'),
    path('providers/<int:pk>/approve/',  views.approve_provider,  name='admin-approve'),
    path('providers/<int:pk>/reject/',   views.reject_provider,   name='admin-reject'),
    path('customers/',                   views.list_customers,    name='admin-customers'),
    path('users/<int:pk>/toggle/',       views.toggle_user,       name='admin-toggle-user'),
    path('bookings/',                    views.list_bookings,     name='admin-bookings'),
]
