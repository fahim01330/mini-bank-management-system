import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from accounts.models import BankAccount


def generate_transaction_reference():
    """
    Generates a unique transaction reference code like TXN-YYYYMMDD-UUIDHEX.
    """
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = uuid.uuid4().hex[:8].upper()
    return f"TXN-{date_str}-{random_str}"


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
    )

    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    transaction_reference = models.CharField(
        max_length=64,
        unique=False,
        db_index=True,
        default=generate_transaction_reference,
        help_text="Reference identifier for the transaction (shared between sender and receiver in transfers)."
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction: DEPOSIT, WITHDRAWAL, or TRANSFER."
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Monetary amount involved in the transaction."
    )
    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="The primary bank account affected by this transaction."
    )
    related_account = models.ForeignKey(
        BankAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='counterparty_transactions',
        help_text="Counterparty bank account involved (for transfers)."
    )
    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Account balance immediately after this transaction was processed."
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='SUCCESS',
        help_text="Execution status of transaction."
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional notes or automatic description of the transaction."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Date and time when the transaction was completed."
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['account', '-timestamp']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.transaction_reference} | {self.transaction_type} | ${self.amount} | {self.account.account_number}"
