from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/v1/auth/',      include('apps.accounts.urls')),
    path('api/v1/providers/', include('apps.providers.urls')),
    path('api/v1/bookings/',  include('apps.bookings.urls')),
    path('api/v1/admin/',     include('apps.admin_panel.urls')),
]
