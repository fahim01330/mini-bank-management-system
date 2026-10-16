from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from accounts.models import BankAccount
from .models import Transaction, generate_transaction_reference
from .serializers import (
    TransactionSerializer,
    DepositSerializer,
    WithdrawSerializer,
    TransferSerializer,
)
from .filters import TransactionFilter
from users.permissions import IsAdminUserOnly


class DepositView(APIView):
    """
    POST: Deposit funds into a customer bank account.
    Rejects zero or negative amounts.
    Records successful deposit in transaction history.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        account = serializer.validated_data['account']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', 'Deposit')

        with transaction.atomic():
            # Lock the account row for safe update
            locked_account = BankAccount.objects.select_for_update().get(id=account.id)
            locked_account.balance += amount
            locked_account.save(update_fields=['balance'])

            txn = Transaction.objects.create(
                transaction_type='DEPOSIT',
                amount=amount,
                account=locked_account,
                balance_after=locked_account.balance,
                status='SUCCESS',
                description=description
            )

        return Response(
            {
                "message": f"Successfully deposited ${amount:.2f} into account {locked_account.account_number}.",
                "transaction": TransactionSerializer(txn).data,
                "current_balance": str(locked_account.balance),
            },
            status=status.HTTP_201_CREATED
        )


class WithdrawView(APIView):
    """
    POST: Withdraw funds from a customer bank account.
    Rejects zero or negative amounts, and prevents withdrawal if balance is insufficient
    or if the daily withdrawal limit is exceeded.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WithdrawSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        account = serializer.validated_data['account']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', 'Withdrawal')

        with transaction.atomic():
            # Lock the account row for safe update and recheck balance
            locked_account = BankAccount.objects.select_for_update().get(id=account.id)

            if locked_account.balance < amount:
                raise ValidationError({
                    "amount": f"Insufficient funds. Available balance is ${locked_account.balance:.2f}."
                })

            locked_account.balance -= amount
            locked_account.save(update_fields=['balance'])

            txn = Transaction.objects.create(
                transaction_type='WITHDRAWAL',
                amount=amount,
                account=locked_account,
                balance_after=locked_account.balance,
                status='SUCCESS',
                description=description
            )

        return Response(
            {
                "message": f"Successfully withdrew ${amount:.2f} from account {locked_account.account_number}.",
                "transaction": TransactionSerializer(txn).data,
                "current_balance": str(locked_account.balance),
            },
            status=status.HTTP_201_CREATED
        )


class TransferView(APIView):
    """
    POST: Transfer money from one account to another account.
    Verifies sender funds, prevents transfer to same account, and ensures atomic
    consistent balance updates and ledger records for both accounts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        from_account = serializer.validated_data['from_account']
        to_account = serializer.validated_data['to_account']
        amount = serializer.validated_data['amount']
        user_description = serializer.validated_data.get('description', '').strip()

        with transaction.atomic():
            # Select and lock both accounts ordered by ID to avoid deadlocks
            first_id, second_id = sorted([from_account.id, to_account.id])
            accounts_map = {
                acc.id: acc
                for acc in BankAccount.objects.select_for_update().filter(id__in=[first_id, second_id])
            }

            locked_from = accounts_map[from_account.id]
            locked_to = accounts_map[to_account.id]

            # Recheck sender funds inside locked block
            if locked_from.balance < amount:
                raise ValidationError({
                    "amount": f"Insufficient funds. Available balance is ${locked_from.balance:.2f}."
                })

            locked_from.balance -= amount
            locked_from.save(update_fields=['balance'])

            locked_to.balance += amount
            locked_to.save(update_fields=['balance'])

            ref = generate_transaction_reference()

            # Record sender transaction
            desc_from = user_description or f"Transfer to {locked_to.account_number}"
            txn_from = Transaction.objects.create(
                transaction_reference=ref,
                transaction_type='TRANSFER',
                amount=amount,
                account=locked_from,
                related_account=locked_to,
                balance_after=locked_from.balance,
                status='SUCCESS',
                description=desc_from
            )

            # Record receiver transaction
            desc_to = user_description or f"Transfer received from {locked_from.account_number}"
            Transaction.objects.create(
                transaction_reference=ref,
                transaction_type='TRANSFER',
                amount=amount,
                account=locked_to,
                related_account=locked_from,
                balance_after=locked_to.balance,
                status='SUCCESS',
                description=desc_to
            )

        return Response(
            {
                "message": f"Successfully transferred ${amount:.2f} to account {locked_to.account_number}.",
                "transaction": TransactionSerializer(txn_from).data,
                "current_balance": str(locked_from.balance),
            },
            status=status.HTTP_201_CREATED
        )


class TransactionHistoryView(generics.ListAPIView):
    """
    GET: View transaction history for accounts belonging to the authenticated customer.
    Supports filtering by:
      - transaction_type (DEPOSIT, WITHDRAWAL, TRANSFER)
      - account_number or account_id
      - start_date and end_date (YYYY-MM-DD)
      - min_amount and max_amount
    Results are paginated.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = TransactionFilter
    ordering_fields = ['timestamp', 'amount']
    search_fields = ['transaction_reference', 'description', 'account__account_number']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff and self.request.query_params.get('all') == 'true':
            return Transaction.objects.all().select_related('account', 'related_account', 'account__owner')
        return Transaction.objects.filter(account__owner=user).select_related(
            'account', 'related_account', 'account__owner'
        )


class AdminTransactionListView(generics.ListAPIView):
    """
    Admin-only endpoint to view, filter, and inspect all transaction records across the bank.
    """
    queryset = Transaction.objects.all().select_related('account', 'related_account', 'account__owner')
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUserOnly]
    filterset_class = TransactionFilter
    ordering_fields = ['timestamp', 'amount', 'balance_after']
    search_fields = ['transaction_reference', 'description', 'account__account_number', 'account__owner__username']
