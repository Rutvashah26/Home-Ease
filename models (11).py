"""
apps/accounts/models.py
Custom User model — roles: customer | provider | admin
Notification model — per-user inbox (mirrors frontend DB.load('notifications'))
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', User.ADMIN)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    CUSTOMER = 'customer'
    PROVIDER = 'provider'
    ADMIN    = 'admin'
    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (PROVIDER, 'Service Provider'),
        (ADMIN,    'Admin'),
    ]

    # core
    email  = models.EmailField(unique=True)
    name   = models.CharField(max_length=120)
    phone  = models.CharField(max_length=20, blank=True)
    role   = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CUSTOMER, db_index=True)

    # location — used by both customers and providers
    city   = models.CharField(max_length=80,  blank=True)
    area   = models.CharField(max_length=120, blank=True)
    state  = models.CharField(max_length=80,  blank=True)

    # django internals
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table    = 'he_users'
        verbose_name = 'User'

    def __str__(self):
        return f'{self.name} <{self.email}> [{self.role}]'

    # convenience
    @property
    def is_customer(self): return self.role == self.CUSTOMER
    @property
    def is_provider(self): return self.role == self.PROVIDER
    @property
    def is_admin_role(self): return self.role == self.ADMIN


class Notification(models.Model):
    """
    In-app notification for a user.
    type: 'green' | 'orange' | 'red'  (matches frontend CSS class)
    """
    GREEN  = 'green'
    ORANGE = 'orange'
    RED    = 'red'
    TYPE_CHOICES = [(GREEN,'Green'), (ORANGE,'Orange'), (RED,'Red')]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    sub        = models.CharField(max_length=400, blank=True)
    type       = models.CharField(max_length=10, choices=TYPE_CHOICES, default=GREEN)
    is_read    = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'he_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.user.name}] {self.title}'
