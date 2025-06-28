from rest_framework import permissions

from .models import ApiKey

class LinuxClientPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    def has_permission(self, request, view):
        # Allow access for staff users (administrators)
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True

        api_key_string = request.META.get('HTTP_API_KEY')
        api_key = ApiKey.objects.filter(key=api_key_string).first()
        if not api_key:
            return False
        permissions = api_key.permissions.split(',')
        if 'linux_client' in permissions:
            return True
        return False
    

class AdministratorPermission(permissions.BasePermission):
    """
    Global permission check for administrator access.
    """

    def has_permission(self, request, view):
        # Allow access for staff users (administrators)
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True
        api_key_string = request.META.get('HTTP_API_KEY')
        api_key = ApiKey.objects.filter(key=api_key_string).first()
        if not api_key:
            return False
        permissions = api_key.permissions.split(',')
        if 'administrator' in permissions:
            return True
        return False