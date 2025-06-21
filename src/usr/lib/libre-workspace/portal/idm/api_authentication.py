from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from .models import ApiKey

class ApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        check_api_key_expirations()
        api_key_string = request.META.get('HTTP_API_KEY')
        api_key = ApiKey.objects.filter(key=api_key_string).first()
        if not api_key:
            raise exceptions.AuthenticationFailed('Invalid API key')
        user = api_key.user
        return (user, None)
    

def check_api_key_expirations():
    from django.utils import timezone
    expired_keys = ApiKey.objects.filter(expiration_date__lt=timezone.now())
    for key in expired_keys:
        key.delete()
        print(f"Deleted expired API key: {key.key}")
    

def remove_all_api_keys_for_user(user_name):
    """
    Remove all API keys for a given user.
    """
    api_keys_to_remove = ApiKey.objects.filter(user__username=user_name)
    for api_key in api_keys_to_remove:
        api_key.delete()
        print(f"Removed API key: {api_key.key} for user: {user_name}")
    print(f"Removed all API keys for user: {user_name}")