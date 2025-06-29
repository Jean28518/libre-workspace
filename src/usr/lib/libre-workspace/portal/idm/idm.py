from django.utils.translation import gettext as _
import string
import random
import os
import idm.ldap as ldap

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
import unix.unix_scripts.unix as unix
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import LinuxClientUser
import subprocess


# user: ldap user, user object or username
def get_user_information(user):
    """Takes a user object, username or LDAP user and returns a dict with user information."""
    user_information = {}
    if type(user) == str:
        if settings.AUTH_LDAP_ENABLED and user.lower() == "administrator":
            user_information = ldap.get_user_information_of_cn("Administrator")
        # If LDAP is enabled AND we get a username which is not "Administrator", then let's get the user_information from LDAP
        elif settings.AUTH_LDAP_ENABLED:
            user_information = ldap.get_user_information_of_cn(user)
        # Otherwise we get the user_information from the local user object (if it exists)
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
    random_password = generate_random_password()
    ldap.set_ldap_user_new_password(user, random_password)
    unix.change_password_for_linux_user(user, random_password)
    print(random_password)
    send_mail(subject=_("New Password (Linux Workstation Central)"), from_email=os.getenv("EMAIL_HOST_USER"), message=_("Your new password is:\n\n%(random_password)s") % {"random_password": random_password}, recipient_list=[email])
    pass


def generate_random_password(length=20, alphanumeric_only=False):
    characters = list(string.ascii_letters + string.digits)
    if not alphanumeric_only:
        characters += list("!@#$%^&*()")
        
    password = []
    for i in range(length):
        password.append(random.choice(characters))

    random.shuffle(password)
    return "".join(password)


def set_user_new_password(username, password):
    # Also returns the local admin user if LDAP is disabled
    user = ldap.get_user_information_of_cn(username)
    if user == None:
        print(_("User not found"))
        return _("User not found")
    # If we got a user_information dict:
    if type(user) == dict:
        message = ldap.set_ldap_user_new_password(user["dn"], password)
        return message
    # Else we got the local user object
    else:
        user.set_password(password)
        user.save()
        return None


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
            print(_("Created superuser 'Administrator' with password '%(password)s'") % {"password": settings.INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP})


def is_2fa_enabled(user):
    return TOTPDevice.objects.filter(user=user).count() > 0


def reset_2fa_for_username(username):
    devices = TOTPDevice.objects.all()
    for device in devices:
        if device.user.username.lower() == username.lower():
            device.delete()
    

def change_superuser_password(new_password):
    """Only changes the password of the django superuser."""
    if settings.AUTH_LDAP_ENABLED:
        pass
    else:
        # Check if user exists
        if not User.objects.filter(username="Administrator").exists():
            print(_("User 'Administrator' does not exist"))
        user = User.objects.get(username="Administrator")
        user.set_password(new_password)
        user.save()
        print(_("Local Administrator password changed"))


def get_admin_user():
    """Returns the user_information dict of the admin user."""
    if settings.AUTH_LDAP_ENABLED:
        return get_user_information("Administrator")
    else:
        user_information = User.objects.get(username="Administrator").__dict__
        user_information["admin"] = True
        user_information["mail"] = user_information["email"]
        user_information["groups"] = ["admin", "Domain Admins"]
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


# Works only when samba is directly installed on the same system this portal is running.
def get_all_linux_users_with_passwords():
    """
    Returns a list of all users with their passwords.
    This is used to check if the user can login with the given password.
    """
    if not settings.AUTH_LDAP_ENABLED:
        return []

    all_users = ldap.ldap_get_all_users()
    all_groups = ldap.ldap_get_all_groups()

    print(all_groups)


    users = []
    for user in all_users:
        user_dn = user.get("dn", "")
        linux_client_user = LinuxClientUser.objects.filter(dn=user_dn.lower()).first()
        if linux_client_user:
            user["yescrypt_hash"] = linux_client_user.yescrypt_hash
        else:
            user["yescrypt_hash"] = None
        user["username"] = user.get("cn", "")

        current_group_dns_of_user = user.get("groups", [])
        # Match the real groups:
        group_return_list = []
        for current_group_dn in current_group_dns_of_user:
            group = next((g for g in all_groups if g.get("dn", "").lower() == current_group_dn.lower()), None)
            if group:
                group_dict = {
                    "dn": group.get("dn", ""),
                    "cn": group.get("cn", ""),
                    "description": group.get("description", ""),
                    "gidNumber": group.get("gidNumber", "")
                }
                group_return_list.append(group_dict)

        user["groups"] = group_return_list
        users.append(user)
    return users


def update_linux_client_password(username, new_password):
    """
    Updates the password for the Linux client user.
    Takes both the username and the new password as strings.
    This function is only used if LDAP is disabled.
    """
    # echo -n "{new_password}" | mkpasswd -m yescrypt -s
    yescrypt_hash = subprocess.run(["mkpasswd", "-m", "yescrypt", "-s"], input=new_password, capture_output=True, text=True).stdout.strip()
    print(yescrypt_hash)

    # Only currently works with LDAP
    if settings.AUTH_LDAP_ENABLED:
        # Update LDAP user
        user_information = ldap.get_user_information_of_cn(username)
        if user_information is None:
            print(_("User not found"))
            return _("User not found")
        linux_client_user = LinuxClientUser.objects.filter(dn=user_information["dn"].lower()).first()
        if linux_client_user is None:
            linux_client_user = LinuxClientUser(dn=user_information["dn"].lower(), yescrypt_hash=yescrypt_hash)
        linux_client_user.yescrypt_hash = yescrypt_hash
        linux_client_user.save()
        print(_("Updated Linux client user password for user: %(username)s with new password hash: %(yescrypt_hash)s") % {"username": username, "yescrypt_hash": yescrypt_hash})
        
   