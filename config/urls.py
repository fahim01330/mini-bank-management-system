"""
URL configuration for Mini Bank Management System API.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API Root providing discoverability for Mini Bank Management System endpoints.
    """
    return Response({
        "project": "Mini Bank Management System API",
        "version": "1.0.0",
        "documentation": "See README.md and Postman Collection",
        "endpoints": {
            "authentication": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/",
                "profile": "/api/profile/",
            },
            "accounts": {
                "list_or_create": "/api/accounts/",
                "detail": "/api/accounts/<id>/",
                "balance": "/api/accounts/<id>/balance/",
                "statement": "/api/accounts/<id>/statement/?format=pdf|csv",
            },
            "transactions": {
                "deposit": "/api/transactions/deposit/",
                "withdraw": "/api/transactions/withdraw/",
                "transfer": "/api/transactions/transfer/",
                "history": "/api/transactions/",
            },
            "admin": {
                "customers": "/api/admin/customers/",
                "accounts": "/api/admin/accounts/",
                "transactions": "/api/admin/transactions/",
                "django_admin_panel": "/admin/",
            }
        }
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('transactions.urls')),
]
