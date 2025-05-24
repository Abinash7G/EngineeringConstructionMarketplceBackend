from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Group

class IsAuthenticatedAdminOrPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if the user is a superuser or in the "Platformadmin" group
        return (
            request.user.is_superuser or
            request.user.groups.filter(name='Platformadmin').exists()
        )