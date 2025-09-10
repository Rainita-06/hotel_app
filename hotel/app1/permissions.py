from rest_framework.permissions import BasePermission


class IsAdminForMaster(BasePermission):
    """
    Custom permission:
    - Only allow admin users to access Master User and Master Location
    - Normal users can access other screens
    """
    def has_permission(self, request, view):
        # Only superusers (admin) can access
        return request.user and request.user.is_staff
