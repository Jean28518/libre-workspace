import string
import random
import os
from .ldap import get_user_dn_by_email, set_ldap_user_new_password, get_user_information_of_cn, is_ldap_user_password_correct

from django.conf import settings
from django.core.mail import send_mail

def get_user_information(user):
    user_information = {}
    if settings.AUTH_LDAP_ENABLED:
        user_information = get_user_information_of_cn(user.ldap_user.dn)
    else:
        user_information["admin"] = user.is_superuser
        user_information["username"] = user.username
        user_information["email"] = user.email
        user_information["first_name"] = user.first_name
        user_information["last_name"] = user.last_name
        user_information["displayName"] = user.first_name + " " + user.last_name
    return user_information


def reset_password_for_email(email):
    user = get_user_dn_by_email(email)
    if user == None:
        return
    random_password = _generate_random_password()
    set_ldap_user_new_password(user, random_password)
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
        message = set_ldap_user_new_password(user.ldap_user.dn, password)
    else:
        message = None
        user.set_password(password)
        user.save()
    return message


def is_user_password_correct(user, password):
    if settings.AUTH_LDAP_ENABLED:
        return is_ldap_user_password_correct(user.ldap_user.dn, password)
    else:
        return user.check_password(password)