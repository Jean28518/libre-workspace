from django.utils import timezone
from .models import ApiKey
from .idm import generate_random_password


def create_api_key(user, name, permissions, expiration_date):
    """
    Create an API key with the given name, rights, and expiration date.

    :param user: The user for whom the API key is being created.
    :param name: The name of the API key.
    :param rights: The rights associated with the API key. Separate multiple rights with commas (e.g., 'linux_client,administrator').
    :param expiration_date: The expiration date of the API key in 'YYYY-MM-DD' format or None or '0' for no expiration.
    """
    api_key = ApiKey()
    api_key.user = user
    api_key.name = name
    api_key.key = generate_random_password(length=64, alphanumeric_only=True)  # Generate a random key
    if expiration_date == None or expiration_date == '0':
        api_key.expiration_date = None
    else:
        try:
            api_key.expiration_date = timezone.datetime.strptime(expiration_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid expiration date format. Use 'YYYY-MM-DD' or '0' for no expiration.")
    api_key.permissions = ','.join(permissions.split(','))
    api_key.save()
    return api_key.key
    
    