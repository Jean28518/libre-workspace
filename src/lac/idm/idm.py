import string
import random
import os
import idm.ldap as ldap

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User


# user: ldap user, user object or username
def get_user_information(user):
    user_information = {}
    if type(user) == str:
        if settings.AUTH_LDAP_ENABLED:
            user_information = ldap.get_user_information_of_cn("Administrator")
        else:
            user = User.objects.get(username=user)
    elif settings.AUTH_LDAP_ENABLED:     
        user_information = ldap.get_user_information_of_cn(user.ldap_user.dn)

    if not settings.AUTH_LDAP_ENABLED:
        user_information["admin"] = user.is_superuser
        user_information["username"] = user.username
        user_information["mail"] = user.email
        user_information["first_name"] = user.first_name
        user_information["last_name"] = user.last_name
        user_information["displayName"] = user.first_name + " " + user.last_name
        
    return user_information


def reset_password_for_email(email):
    user = ldap.get_user_dn_by_email(email)
    if user == None:
        return
    random_password = _generate_random_password()
    ldap.set_ldap_user_new_password(user, random_password)
    print(random_password)
    send_mail(subject="Neues Passwort (Linux-Arbeisplatz Zentrale)", from_email=os.getenv("EMAIL_HOST_USER"), message=f"Das neue Passwort ist:\n\n{random_password}", recipient_list=[email])
    pass


def _generate_random_password():
    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
        
    password = []
    for i in range(20):
        password.append(random.choice(characters))

    random.shuffle(password)
    return "".join(password)


def set_user_new_password(user, password):
    if settings.AUTH_LDAP_ENABLED:
        message = ldap.set_ldap_user_new_password(user.ldap_user.dn, password)
    else:
        message = None
        user.set_password(password)
        user.save()
    return message


def is_user_password_correct(user, password):
    if settings.AUTH_LDAP_ENABLED:
        return ldap.is_ldap_user_password_correct(user.ldap_user.dn, password)
    else:
        return user.check_password(password)
    

# Also ensures that a superuser exists if LDAP is disabled
def ensure_superuser_exists():
    if not settings.AUTH_LDAP_ENABLED:
        if User.objects.filter(is_superuser=True).count() == 0:
            User.objects.create_superuser(
                username="Administrator",
                first_name="Administrator",
                password=settings.INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP,
                email="",
            )
            print("Created superuser 'Administrator' with password '{}'".format(settings.INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP))



def change_superuser_password(new_password):
    """Only changes the password of the django superuser."""
    if settings.AUTH_LDAP_ENABLED:
        pass
    else:
        user = User.objects.get(username="Administrator")
        user.set_password(new_password)
        user.save()


def get_admin_user():
    """Returns the user_information dict of the admin user."""
    if settings.AUTH_LDAP_ENABLED:
        return get_user_information("Administrator")
    else:
        user_information = User.objects.get(username="Administrator").__dict__
        user_information["admin"] = True
        user_information["mail"] = user_information["email"]
        return user_information
    

def update_user(username, user_information):
    """
    Only use this, if LDAP is disabled
    """

    if settings.AUTH_LDAP_ENABLED:
        # Update LDAP user
        pass
    else:
        # Update Django user
        user = User.objects.get(username=username)
        user.first_name = user_information["first_name"]
        user.last_name = user_information["last_name"]
        user.email = user_information["mail"]
        user.save()
