from rest_framework import permissions
from django.conf import settings

class ConditionalAuthentication(permissions.BasePermission):
    def has_permission(self, request, view):
        # Get the setting name from view attributes
        setting_name = getattr(view, 'auth_setting', None)
        
        if not setting_name:
            return False
            
        # Get the actual value from Django settings
        requires_auth = getattr(settings, setting_name, True)
        
        if requires_auth:
            return request.user and request.user.is_authenticated
        return True  # Allow unauthenticated access if setting is False