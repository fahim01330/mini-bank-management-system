import random
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


def generate_unique_account_number():
    """
    Generates a unique 10-digit bank account number starting with '10'.
    """
    from .models import BankAccount
    while True:
        # e.g., 1000000000 to 1099999999
        number = f"10{random.randint(10000000, 99999999)}"
        if not BankAccount.objects.filter(account_number=number).exists():
            return number


class BankAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('SAVINGS', 'Savings'),
        ('CURRENT', 'Current'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('CLOSED', 'Closed'),
    )

    account_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        default=generate_unique_account_number,
        help_text="Unique 10-digit bank account number."
    )
    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default='SAVINGS',
        help_text="Type of bank account (Savings or Current)."
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current available account balance."
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accounts',
        help_text="Customer owning this bank account."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="Operational status of the account."
    )
    daily_withdrawal_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('50000.00'),
        help_text="Maximum allowed withdrawals per 24 hours."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=Decimal('0.00')),
                name='bank_account_balance_non_negative'
            )
        ]

    def __str__(self):
        return f"{self.account_number} ({self.get_account_type_display()}) - {self.owner.username}"

    def clean(self):
        if self.balance < Decimal('0.00'):
            raise ValidationError("Account balance cannot be negative.")

    def is_active(self):
        return self.status == 'ACTIVE'
