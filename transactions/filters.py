import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    transaction_type = django_filters.ChoiceFilter(choices=Transaction.TRANSACTION_TYPE_CHOICES)
    account_number = django_filters.CharFilter(field_name='account__account_number', lookup_expr='exact')
    account_id = django_filters.NumberFilter(field_name='account__id', lookup_expr='exact')
    start_date = django_filters.DateFilter(field_name='timestamp', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='timestamp', lookup_expr='date__lte')
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'account_number',
            'account_id',
            'start_date',
            'end_date',
            'min_amount',
            'max_amount',
            'status',
        ]
