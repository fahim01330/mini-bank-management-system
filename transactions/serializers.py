from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from rest_framework import serializers

from accounts.models import BankAccount
from .models import Transaction, generate_transaction_reference


class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    related_account_number = serializers.CharField(
        source='related_account.account_number',
        read_only=True,
        default=None
    )
    account_owner_username = serializers.CharField(source='account.owner.username', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_reference',
            'transaction_type',
            'amount',
            'account',
            'account_number',
            'account_owner_username',
            'related_account',
            'related_account_number',
            'balance_after',
            'status',
            'description',
            'timestamp',
        ]
        read_only_fields = fields


class DepositSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        help_text="ID of the bank account to deposit into."
    )
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Deposit amount (must be positive)."
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        default="Deposit",
        help_text="Optional transaction note."
    )

    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Deposit amount must be strictly positive (greater than 0.00).")
        return value

    def validate_account(self, account):
        if not account.is_active():
            raise serializers.ValidationError("Deposit cannot be processed on an inactive or closed account.")
        return account

    def validate(self, attrs):
        request = self.context.get('request')
        account = attrs.get('account')
        if request and not request.user.is_staff and account.owner != request.user:
            raise serializers.ValidationError({"account": "You can only deposit into your own accounts."})
        return attrs


class WithdrawSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        help_text="ID of the bank account to withdraw from."
    )
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Withdrawal amount (must be positive)."
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        default="Withdrawal",
        help_text="Optional transaction note."
    )

    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Withdrawal amount must be strictly positive (greater than 0.00).")
        return value

    def validate_account(self, account):
        if not account.is_active():
            raise serializers.ValidationError("Withdrawal cannot be processed on an inactive or closed account.")
        return account

    def validate(self, attrs):
        request = self.context.get('request')
        account = attrs.get('account')
        amount = attrs.get('amount')

        # Ownership check
        if request and not request.user.is_staff and account.owner != request.user:
            raise serializers.ValidationError({"account": "You can only withdraw from your own accounts."})

        # Insufficient funds check
        if account.balance < amount:
            raise serializers.ValidationError({
                "amount": f"Insufficient funds. Current balance is ${account.balance:.2f}, but requested withdrawal is ${amount:.2f}."
            })

        # Daily withdrawal limit check
        since_24h = timezone.now() - timedelta(hours=24)
        total_withdrawn_24h = Transaction.objects.filter(
            account=account,
            transaction_type='WITHDRAWAL',
            status='SUCCESS',
            timestamp__gte=since_24h
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        if total_withdrawn_24h + amount > account.daily_withdrawal_limit:
            remaining_limit = max(Decimal('0.00'), account.daily_withdrawal_limit - total_withdrawn_24h)
            raise serializers.ValidationError({
                "amount": (
                    f"Daily withdrawal limit of ${account.daily_withdrawal_limit:.2f} exceeded. "
                    f"Already withdrawn in last 24h: ${total_withdrawn_24h:.2f}. "
                    f"Remaining limit: ${remaining_limit:.2f}."
                )
            })

        return attrs


class TransferSerializer(serializers.Serializer):
    from_account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        help_text="ID of the source bank account."
    )
    to_account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        help_text="ID of the destination bank account."
    )
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Transfer amount (must be positive)."
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        default="",
        help_text="Optional transfer note."
    )

    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Transfer amount must be strictly positive (greater than 0.00).")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        from_account = attrs.get('from_account')
        to_account = attrs.get('to_account')
        amount = attrs.get('amount')

        # Same account check
        if from_account == to_account:
            raise serializers.ValidationError({
                "to_account": "Cannot transfer money to the same bank account."
            })

        # Status check
        if not from_account.is_active():
            raise serializers.ValidationError({"from_account": "Source account is inactive or closed."})
        if not to_account.is_active():
            raise serializers.ValidationError({"to_account": "Destination account is inactive or closed."})

        # Ownership check
        if request and not request.user.is_staff and from_account.owner != request.user:
            raise serializers.ValidationError({"from_account": "You can only transfer money from your own account."})

        # Balance check
        if from_account.balance < amount:
            raise serializers.ValidationError({
                "amount": f"Insufficient funds. Current balance in source account is ${from_account.balance:.2f}, but requested transfer is ${amount:.2f}."
            })

        return attrs
