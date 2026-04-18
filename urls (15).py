from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('register/customer/', views.register_customer,    name='register-customer'),
    path('login/',             views.login_view,           name='login'),
    path('logout/',            views.logout_view,          name='logout'),
    path('token/refresh/',     TokenRefreshView.as_view(), name='token-refresh'),
    # Profile
    path('profile/',           views.ProfileView.as_view(), name='profile'),
    path('change-password/',   views.change_password,       name='change-password'),
    # Notifications
    path('notifications/',              views.list_notifications,     name='notif-list'),
    path('notifications/read/',         views.mark_notifications_read,name='notif-read'),
    path('notifications/unread-count/', views.unread_count,           name='notif-count'),
]
