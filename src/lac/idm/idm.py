import string
import random
import os
from .ldap import get_user_dn_by_email, set_ldap_user_new_password

from django.core.mail import send_mail

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