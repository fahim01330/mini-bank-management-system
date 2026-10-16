from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    UserProfileView,
    AdminCustomerListView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='user-register'),
    path('auth/login/', LoginView.as_view(), name='user-login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('admin/customers/', AdminCustomerListView.as_view(), name='admin-customers'),
]
