from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base
from .models import User, Notification

@admin.register(User)
class UserAdmin(Base):
    list_display  = ['email', 'name', 'role', 'phone', 'city', 'is_active', 'date_joined']
    list_filter   = ['role', 'is_active']
    search_fields = ['email', 'name', 'phone']
    ordering      = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Info', {'fields': ('name', 'phone', 'city', 'area', 'state')}),
        ('Role', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = ((None, {'classes':('wide',), 'fields':('email','name','role','password1','password2')}),)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'is_read', 'created_at']
    list_filter  = ['type', 'is_read']
