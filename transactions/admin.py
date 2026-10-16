from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_reference',
        'transaction_type',
        'amount',
        'account',
        'related_account',
        'balance_after',
        'status',
        'timestamp',
    )
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = (
        'transaction_reference',
        'account__account_number',
        'account__owner__username',
        'related_account__account_number',
        'description',
    )
    readonly_fields = (
        'transaction_reference',
        'transaction_type',
        'amount',
        'account',
        'related_account',
        'balance_after',
        'status',
        'description',
        'timestamp',
    )
    ordering = ('-timestamp',)
