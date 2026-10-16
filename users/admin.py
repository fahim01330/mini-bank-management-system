from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Customer Additional Information', {
            'fields': ('phone_number', 'address', 'date_of_birth')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Customer Additional Information', {
            'fields': ('email', 'phone_number', 'address', 'date_of_birth')
        }),
    )
