from django.urls import path
from .views import (
    BankAccountListCreateView,
    BankAccountDetailView,
    BankAccountBalanceView,
    BankAccountStatementView,
    AdminBankAccountListView,
)

urlpatterns = [
    path('accounts/', BankAccountListCreateView.as_view(), name='account-list-create'),
    path('accounts/<int:pk>/', BankAccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/balance/', BankAccountBalanceView.as_view(), name='account-balance'),
    path('accounts/<int:pk>/statement/', BankAccountStatementView.as_view(), name='account-statement'),
    path('admin/accounts/', AdminBankAccountListView.as_view(), name='admin-accounts'),
]
