from django.utils.dateparse import parse_date
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound

from .models import BankAccount
from .serializers import (
    BankAccountSerializer,
    BankAccountBalanceSerializer,
    AdminBankAccountSerializer,
)
from users.permissions import IsOwnerOrAdmin, IsAdminUserOnly
from .utils import export_statement_csv, export_statement_pdf


class BankAccountListCreateView(generics.ListCreateAPIView):
    """
    GET: List all bank accounts belonging to the authenticated customer.
    POST: Create a new bank account (Savings or Current) with an optional initial deposit.
    """
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff and self.request.query_params.get('all') == 'true':
            return BankAccount.objects.all().select_related('owner')
        return BankAccount.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save()


class BankAccountDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve detailed information for a specific bank account.
    Restricted to account owner or administrator.
    """
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        account = super().get_object()
        self.check_object_permissions(self.request, account)
        return account


class BankAccountBalanceView(APIView):
    """
    GET: Check the real-time balance of a specific bank account.
    Restricted to account owner or administrator.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            account = BankAccount.objects.get(pk=pk)
        except BankAccount.DoesNotExist:
            raise NotFound({"error": "Bank account not found."})

        if not request.user.is_staff and account.owner != request.user:
            raise PermissionDenied({"error": "You do not have permission to view this account's balance."})

        serializer = BankAccountBalanceSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework.renderers import BaseRenderer, JSONRenderer

class CSVRenderer(BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class PDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class BankAccountStatementView(APIView):
    """
    GET: Generate and download an account statement in PDF or CSV format.
    Supports query parameters:
      - format: 'pdf' (default) or 'csv'
      - start_date: YYYY-MM-DD
      - end_date: YYYY-MM-DD
    """
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [PDFRenderer, CSVRenderer, JSONRenderer]

    def perform_content_negotiation(self, request, force=False):
        # Return fallback renderer to gracefully handle direct file downloads
        return (PDFRenderer(), 'application/pdf')

    def get(self, request, pk):
        try:
            account = BankAccount.objects.get(pk=pk)
        except BankAccount.DoesNotExist:
            raise NotFound({"error": "Bank account not found."})

        if not request.user.is_staff and account.owner != request.user:
            raise PermissionDenied({"error": "You do not have permission to export statements for this account."})

        file_format = request.query_params.get('format', 'pdf').lower()
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        transactions = account.transactions.all().select_related('related_account').order_by('timestamp')

        if start_date_str:
            parsed_start = parse_date(start_date_str)
            if parsed_start:
                transactions = transactions.filter(timestamp__date__gte=parsed_start)

        if end_date_str:
            parsed_end = parse_date(end_date_str)
            if parsed_end:
                transactions = transactions.filter(timestamp__date__lte=parsed_end)

        if file_format == 'csv':
            return export_statement_csv(account, transactions, start_date_str, end_date_str)
        else:
            return export_statement_pdf(account, transactions, start_date_str, end_date_str)


class AdminBankAccountListView(generics.ListAPIView):
    """
    Admin-only endpoint to view, search, and filter all bank accounts across all customers.
    """
    queryset = BankAccount.objects.all().select_related('owner')
    serializer_class = AdminBankAccountSerializer
    permission_classes = [IsAdminUserOnly]
    search_fields = ['account_number', 'owner__username', 'owner__email']
    filterset_fields = ['account_type', 'status']
    ordering_fields = ['balance', 'created_at']
