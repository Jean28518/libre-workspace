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
    