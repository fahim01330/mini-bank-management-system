from decimal import Decimal
from rest_framework import serializers
from .models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    initial_deposit = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
        write_only=True,
        help_text="Optional initial deposit amount when opening account."
    )

    class Meta:
        model = BankAccount
        fields = [
            'id',
            'account_number',
            'account_type',
            'balance',
            'status',
            'daily_withdrawal_limit',
            'owner',
            'owner_username',
            'owner_email',
            'initial_deposit',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'account_number', 'balance', 'owner', 'created_at', 'updated_at']

    def validate_initial_deposit(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Initial deposit amount cannot be negative.")
        return value

    def create(self, validated_data):
        initial_deposit = validated_data.pop('initial_deposit', Decimal('0.00'))
        user = self.context['request'].user
        validated_data['owner'] = user
        validated_data['balance'] = initial_deposit

        account = BankAccount.objects.create(**validated_data)

        # Record initial deposit transaction if amount > 0
        if initial_deposit > Decimal('0.00'):
            from transactions.models import Transaction
            Transaction.objects.create(
                transaction_type='DEPOSIT',
                amount=initial_deposit,
                account=account,
                balance_after=initial_deposit,
                status='SUCCESS',
                description="Initial opening deposit"
            )

        return account


class BankAccountBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            'id',
            'account_number',
            'account_type',
            'balance',
            'status',
            'updated_at',
        ]
        read_only_fields = ['id', 'account_number', 'account_type', 'balance', 'status', 'updated_at']


class AdminBankAccountSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            'id',
            'account_number',
            'account_type',
            'balance',
            'status',
            'daily_withdrawal_limit',
            'owner',
            'owner_username',
            'owner_email',
            'created_at',
            'updated_at',
        ]
