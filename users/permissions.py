from rest_framework import permissions


class IsAdminUserOnly(permissions.BasePermission):
    """
    Allows access only to admin/staff users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin staff to access/edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # For User model instance
        if hasattr(obj, 'username'):
            return obj == request.user
        # For BankAccount model instance
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        # For Transaction model instance
        if hasattr(obj, 'account'):
            return obj.account.owner == request.user or (
                obj.related_account and obj.related_account.owner == request.user
            )
        return False
