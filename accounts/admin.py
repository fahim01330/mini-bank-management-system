from django.contrib import admin
from .models import BankAccount


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'owner', 'account_type', 'balance', 'status', 'daily_withdrawal_limit', 'created_at')
    list_filter = ('account_type', 'status', 'created_at')
    search_fields = ('account_number', 'owner__username', 'owner__email', 'owner__first_name', 'owner__last_name')
    readonly_fields = ('account_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)
