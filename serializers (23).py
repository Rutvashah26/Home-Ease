from django.urls import path
from . import views

urlpatterns = [
    path('',                       views.create_booking,   name='booking-create'),
    path('mine/',                  views.my_bookings,       name='booking-mine'),
    path('requests/',              views.provider_requests, name='booking-requests'),
    path('provider-stats/',        views.provider_stats,    name='booking-prov-stats'),
    path('<int:pk>/',              views.booking_detail,    name='booking-detail'),
    path('<int:pk>/cancel/',       views.cancel_booking,    name='booking-cancel'),
    path('<int:pk>/accept/',       views.accept_booking,    name='booking-accept'),
    path('<int:pk>/decline/',      views.decline_booking,   name='booking-decline'),
    path('<int:pk>/complete/',     views.complete_booking,  name='booking-complete'),
]
