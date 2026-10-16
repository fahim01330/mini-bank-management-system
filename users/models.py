from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.email})"
