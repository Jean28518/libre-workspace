import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
import django_auth_ldap.backend
from django_auth_ldap.backend import LDAPBackend

import idm.idm

from .forms import BasicUserForm, PasswordForm, PasswordResetForm, AdministratorUserForm, AdministratorUserEditForm, GroupCreateForm, GroupEditForm, OIDCClientForm, TOTPChallengeForm, ApiKeyForm
from .ldap import get_user_information_of_cn, is_ldap_user_password_correct, set_ldap_user_new_password, ldap_get_all_users, ldap_create_user, ldap_update_user, ldap_delete_user, ldap_get_all_groups, ldap_create_group, ldap_update_group, ldap_get_group_information_of_cn, ldap_delete_group, is_user_in_group, ldap_remove_user_from_group, ldap_add_user_to_group, get_user_dn_by_email, ldap_get_cn_of_dn, ldap_enable_user, ldap_disable_user
from .idm import reset_password_for_email, get_user_information, set_user_new_password, is_user_password_correct, generate_random_password
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import idm.challenges
import unix.unix_scripts.unix as unix
from oidc_provider.models import Client
import lac.templates as templates
from django.urls import reverse
from django_otp.forms import OTPTokenForm
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
from base64 import b32encode
import lac.templates
import random
import datetime
from .oidc_provider_settings import add_oidc_provider_client
from .models import ApiKey
from .serializer import UserSerializer, GroupSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework import permissions
from rest_framework.decorators import action




def signal_handler(context, user, request, exception, **kwargs):
    print("Context: " + str(context) + "\nUser: " + str(user) + "\nRequest: " + str(request) + "\nException: " + str(exception))

django_auth_ldap.backend.ldap_error.connect(signal_handler)


# Create your views here.
@login_required
def dashboard(request):
    user_information = get_user_information(request.user)
    challenges = idm.challenges.get_all_libre_workspace_challenges(request.user)
    desktop_module_active = unix.is_desktop_installed()
    # Only take the last three challenges because we don't want to overwhelm the user
    if len(challenges) > 3:
        challenges = challenges[-3:]
    return render(request, "idm/dashboard.html", {"request": request, "user_information": user_information, "ldap_enabled": settings.AUTH_LDAP_ENABLED, "challenges": challenges, "desktop_module_active": desktop_module_active})


# We have to set login_page=True to prevent the base template from displaying the login button
login_tries = []
banned_ips = {}
totp_challenge = {}
def user_login(request):
    # Ban IPs that have tried to login more than 5 times for 30 minutes
    _clear_old_login_tries_and_banned_ips()
    ip_adress = request.META.get('REMOTE_ADDR')
    if _get_login_tries(ip_adress) > 5 and not ip_adress in banned_ips.keys():
        banned_ips[ip_adress] = datetime.datetime.now()
    if ip_adress in banned_ips.keys():
        return render(request, 'idm/login.html', {'message': "Zu viele Anmeldeversuche! Bitte versuchen Sie es später erneut.", "hide_login_button": True})
    
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == 'POST':
        # If the request is a totp challenge from the last 5 minutes
        # And also make sure that this is definitely not the user login with username password field
        (timestamp, user) = totp_challenge.get(request.session.session_key, ((datetime.datetime.now() - datetime.timedelta(minutes=10) ), request.user))
        if timestamp.timestamp() > (datetime.datetime.now() - datetime.timedelta(minutes=5)).timestamp() and request.POST.get("username", "") == "":
            totp_challenge.pop(request.session.session_key)
            form = TOTPChallengeForm(request.POST)
            device = TOTPDevice.objects.get(id=request.POST.get("totp_device", ""))
            print("Request POST: " + str(request.POST))
            if device.verify_token(request.POST.get("totp_code", "")):
                print("TOTP code is correct")
                login(request, user)
                if request.GET.get("next", "") != "":
                    return HttpResponseRedirect(request.GET['next'])
                else: 
                    return redirect("index")
            else:
                print("TOTP code is not correct: " + request.POST.get("totp_code", ""))
                # return lac.templates.message(request, "Der TOTP-Code ist nicht korrekt! Versuchen Sie es erneut.", "login")
                return get_totp_challenge_site(request, user, "Fehler: Der TOTP-Code ist nicht korrekt! Versuchen Sie es erneut.")

        username = request.POST['username']

        # Check if user entered email address, if so, convert to username
        if "@" in username and "." in username:
            userdn = get_user_dn_by_email(username)
            if userdn == None:
                login_tries.append((ip_adress, datetime.datetime.now()))
                return render(request, 'idm/login.html', {'message': "Anmeldung fehlgeschlagen! Bitte versuchen Sie es mit Ihrem Nutzernamen.", "login_page": True, "username": username})
            username = ldap_get_cn_of_dn(userdn)

        user = authenticate(username=username, password=request.POST['password'])
        if user and user.is_authenticated:
            print("User is authenticated.")
            
            if user.totpdevice_set.all().count() > 0:
                return get_totp_challenge_site(request, user)

            login(request, user)
            if request.GET.get("next", "") != "":
                return HttpResponseRedirect(request.GET['next'])
            else: 
                return redirect("index")
        else:
            login_tries.append((ip_adress, datetime.datetime.now()))
            print("User is not authenticated")
            return render(request, 'idm/login.html', {'message': "Anmeldung fehlgeschlagen! Bitte versuchen Sie es erneut.", "login_page": True, "username": username})
        
    message = idm.ldap.is_ldap_fine_and_working()
    username = ""

    if message == None:
        # If only one user exists, we can directly set the username
        if len(ldap_get_all_users()) <= 1:
            username = "Administrator"
    
    return render(request, "idm/login.html", {"request": request, "hide_login_button": True, "message": message, "username": username})

def get_totp_challenge_site(request, user, message=""):
    totp_challenge[request.session.session_key] = (datetime.datetime.now(), user)
    form = TOTPChallengeForm()
    # Populate choice field with all totp devices of the user
    form.fields["totp_device"].choices = [(device.id, device.name) for device in user.totpdevice_set.all()]
    return render(request, "lac/generic_form.html", {"form": form, "user": user, "message": message, "heading": "2-Faktor Authentifizierung", "action": "Anmelden", "hide_buttons_top": True, "hide_login_button": True})

@login_required
def otp_settings(request):
    # Get all totp devices of the user
    totp_devices = []
    for device in request.user.totpdevice_set.all():
        totp_devices.append(device)
    overview = lac.templates.process_overview_dict({
        "heading": "2-Faktor-Authentifizierung",
        "element_name": "TOTP-Gerät",
        "element_url_key": "id",
        "elements": totp_devices,
        "t_headings": ["Name"],
        "t_keys": ["name"],
        "add_url_name": "create_totp_device",
        # "edit_url_name": "edit_totp_device",
        "delete_url_name": "delete_totp_device",
    })
    return render(request, "lac/overview_x.html", {"overview": overview})

user_totp_device_challenges = {}
@login_required
def create_totp_device(request):
    username = request.user.get_username()
    if request.method == 'POST':
        if username in user_totp_device_challenges.keys():
            device = user_totp_device_challenges[username]
        else:
            return lac.templates.message(request, "Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.", "create_totp_device")
        # Check the totp code the user entered
        totp_code = request.POST.get("totp_code", "").replace(" ", "")
        if len(totp_code) != 6:
            return lac.templates.message(request, "Der TOTP-Code muss 6 Ziffern lang sein!", "create_totp_device")
        # If we are here we have to remove the challange because also on a wrong verify the device would save to the user
        user_totp_device_challenges.pop(username)
        if not device.verify_token(totp_code):
            device.delete()
            return lac.templates.message(request, "Der TOTP-Code ist nicht korrekt! Versuchen Sie es erneut.", "create_totp_device")
        
        device.name = request.POST.get("device_name", device.name)
        device.confirmed = True
        device.save()
        
        # Remove the QR code image
        random_appendix = user_totp_device_challenges.get(username+"_random_appendix", "")
        if random_appendix != "":
            for file in os.listdir(settings.MEDIA_ROOT):
                if file.startswith("totp_" + str(random_appendix)):
                    os.remove(settings.MEDIA_ROOT + "/" + file)
            user_totp_device_challenges.pop(username+"_random_appendix")
        return lac.templates.message(request, "Erfolgreich. 2-Faktor Authentifizierung erfolgreich eingerichtet.", "otp_settings")


    device = TOTPDevice(user=request.user, name="TOTP (Authenticator App)")

    # Check if the user has a totp device challenge
    if username in user_totp_device_challenges.keys():
        device = user_totp_device_challenges[username]
       
    # Create a new totp device for the user
    user_totp_device_challenges[username] = device

    baseurl_of_libre_workspace = unix.get_env_sh_variables().get("DOMAIN", "")

    url = device.config_url
    url = url.replace(username, "Libre Workspace: " + baseurl_of_libre_workspace + " - " + username)

    random_appendix = random.randint(100000, 999999)
    user_totp_device_challenges[username+"_random_appendix"] = random_appendix

    # Generate QR code with qrcode module
    img = qrcode.make(url)
    img.save(settings.MEDIA_ROOT + f"/totp_{random_appendix}.png")

    base32_code = str(b32encode(device.bin_key))[2:-1]

    return render(request, "idm/add_new_totp_device.html", {"base32_code": base32_code, "img": settings.MEDIA_URL + f"totp_{random_appendix}.png", "device_name": device.name})

    pass

@login_required
def delete_totp_device(request, id):
    user = request.user
    device = TOTPDevice.objects.get(id=id)
    # Check if the user is allowed to delete the device
    devices_of_user = user.totpdevice_set.all()
    if not device in devices_of_user:
        return lac.templates.message(request, "Sie sind nicht berechtigt, dieses Gerät zu löschen!", "otp_settings")
    device.delete()
    # Also remove all totp_*.png files
    for file in os.listdir(settings.MEDIA_ROOT):
        if file.startswith("totp_" + str(id)):
            os.remove(settings.MEDIA_ROOT + "/" + file)
    return redirect(otp_settings)

def _clear_old_login_tries_and_banned_ips():
    """Clears login tries that are older than 5 minutes, and banned IPs that are older than 30 minutes."""
    for i in range(len(login_tries)):
        if datetime.datetime.now() - login_tries[i][1] > datetime.timedelta(minutes=5):
            login_tries.pop(i)
            i -= 1
    for ip in banned_ips.keys():
        if datetime.datetime.now() - banned_ips[ip] > datetime.timedelta(minutes=30):
            banned_ips.pop(ip)
    for session_key in totp_challenge.keys():
        (timestamp, user) = totp_challenge[session_key]
        if datetime.datetime.now() - timestamp > datetime.timedelta(minutes=5):
            totp_challenge.pop(session_key)


def _get_login_tries(ip):
    count = 0
    for i in range(len(login_tries)):
        if login_tries[i][0] == ip:
            count += 1
    return count

def user_logout(request):
    logout(request)
    return redirect("index")


@login_required
def user_settings(request):
    
    if request.method == 'POST':
        form = BasicUserForm(request.POST)
        if form.is_valid():
            # Because when the user is setting his own settings, the user is enabled for sure :)
            form.cleaned_data["enabled"] = True
            form.cleaned_data["admin"] = request.user.is_superuser
            ldap_update_user(request.user.username, form.cleaned_data)
        form.cleaned_data.update({"username": request.user.username})
        form = BasicUserForm(initial=form.cleaned_data)
        if not settings.AUTH_LDAP_ENABLED:
            form.fields["displayName"].disabled = True
        return render(request, "idm/user_settings.html", {"form": form, "message": "Die Änderungen wurden erfolgreich gespeichert!"})

    else:
        user_information = get_user_information(request.user)
        form = BasicUserForm(initial=user_information)
        if not settings.AUTH_LDAP_ENABLED:
            form.fields["displayName"].disabled = True
        return render(request, "idm/user_settings.html", {"form": form})    


def user_password_reset(request):
    message = ""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            reset_password_for_email(form.cleaned_data["email"])
            message = "Sollte die E-Mail-Adresse in unserem System existieren, wurde eine E-Mail mit einem Link zum Zurücksetzen des Passworts versendet."
        else:
            message = "Bitte geben Sie eine gültige E-Mail-Adresse ein."
    form = PasswordResetForm()
    return render(request, "idm/reset_password.html", {"form": form, "message": message})

@login_required
def change_password(request):
    if request.user.username.lower() == "administrator":
        return redirect("critical_system_configuration")
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        message = ""
        if form.is_valid():
            if form.cleaned_data["new_password"] == form.cleaned_data["new_password_repeat"]:
                if is_user_password_correct(request.user, form.cleaned_data["old_password"]):
                    message = set_user_new_password(request.user.username, form.cleaned_data["new_password"])
                    if message == None:
                        message = "Das Passwort wurde erfolgreich geändert!"
                else:
                    message = "Das alte Passwort ist nicht korrekt!"
            else:
                message = "Die neuen Passwörter stimmen nicht überein!"
        return render(request, "idm/change_password.html", {"form": form, "message": message})
    else:
        form = PasswordForm()
        return render(request, "idm/change_password.html", {"form": form})
    

@staff_member_required(login_url=settings.LOGIN_URL)
def reset_2fa(request, username):
    idm.idm.reset_2fa_for_username(username)
    return lac.templates.message(request, f"2-Faktor-Authentifizierung für {username} erfolgreich zurückgesetzt!", "user_overview")


@staff_member_required(login_url=settings.LOGIN_URL)
def user_overview(request):
    users = ldap_get_all_users()
    print(users)
    return render(request, "idm/admin/user_overview.html", {"users": users})

@staff_member_required(login_url=settings.LOGIN_URL)
def create_user(request):
    message = ""
    form = AdministratorUserForm()
    if request.method == 'POST':
        form = AdministratorUserForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            user_information = form.cleaned_data
            message = ldap_create_user(user_information)
            if message == None:
                username = user_information.get("username", "")
                unix.desktop_add_user(username, "", user_information.get("admin", False))
                message = f"Benutzer '{username}' erfolgreich erstellt!"
                # Reset form
                form = AdministratorUserForm()
        else:
            print("Form is not valid")
            print(form.errors)
            message = form.errors

    return render(request, "lac/create_x.html", {"form": form, "message": message, "type": "Benutzer", "url": reverse("user_overview")})

    
@staff_member_required(login_url=settings.LOGIN_URL)
def edit_user(request, cn):
    message = ""
    form_data = get_user_information_of_cn(cn)
    if request.method == 'POST':
        form = AdministratorUserEditForm(request.POST)
        if form.is_valid():
            user_information = form.cleaned_data
            pw_message = ""
            if user_information["password"] != "":
                pw_message = set_ldap_user_new_password(cn, user_information["password"])
                if pw_message == None:
                    pw_message = unix.change_password_for_linux_user(cn, user_information["password"])
                if pw_message == None:
                    pw_message = f"Passwort erfolgreich geändert!"
            user_information.pop("password")
            message = ldap_update_user(cn, user_information)
            if message == None:
                message = f"Änderungen erfolgreich gespeichert!"
            message = message + "<br>" + pw_message
        else:
            message = form.errors
        form_data = form.cleaned_data
    form = AdministratorUserEditForm()
    if form_data != {}:
        form = AdministratorUserEditForm(form_data)
    form.fields["guid"].initial = form_data.get("guid", "")
    return render(request, "idm/admin/edit_user.html", {"form": form, "message": message, "cn": cn})#

@staff_member_required(login_url=settings.LOGIN_URL)
def delete_user(request, cn):
    print(ldap_delete_user(cn))
    unix.desktop_remove_user(cn)
    return redirect(user_overview)

@staff_member_required(login_url=settings.LOGIN_URL)
def group_overview(request):
    groups = ldap_get_all_groups()
    return render(request, "idm/admin/group_overview.html", {"groups": groups})

@staff_member_required(login_url=settings.LOGIN_URL)
def create_group(request):
    message = ""
    form_data = {}
    if request.method == 'POST':
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group_information = form.cleaned_data
            message = ldap_create_group(group_information)
            if message == None:
                if form.cleaned_data.get("nextcloud_groupfolder", False):
                    message = unix.create_nextcloud_groupfolder(group_information["cn"])
                if message == None:
                    cn = group_information.get("cn", "")
                    message = f"Gruppe '{cn}' erfolgreich erstellt!"
        else:
            print("Form is not valid")
            print(form.errors)
            message = form.errors
            form_data = form.cleaned_data
    
    form = GroupCreateForm()
    if form_data != {}:
        form = GroupCreateForm(form_data)
    return render(request, "idm/admin/create_group.html", {"form": form, "message": message})
    

@staff_member_required(login_url=settings.LOGIN_URL)
def edit_group(request, cn):
    message = ""
    form_data = ldap_get_group_information_of_cn(cn)
    if request.method == 'POST':
        form = GroupEditForm(request.POST)
        if form.is_valid():
            group_information = form.cleaned_data
            message = ldap_update_group(cn, group_information)
            if form.cleaned_data.get("nextcloud_groupfolder", False) and not unix.nextcloud_groupfolder_exists(cn):
                message = unix.create_nextcloud_groupfolder(cn)
            if form.cleaned_data.get("nextcloud_groupfolder", False) == False and unix.nextcloud_groupfolder_exists(cn):
                message = "Nextcloud-Gruppenordner wird nicht gelöscht (evtl. wichtige Daten enthalten), bitte manuell im Nextcloud-Admin-Interface löschen."
            if message == None:
                message = f"Änderungen erfolgreich gespeichert!"
        else:
            message = form.errors
        form_data = form.cleaned_data
    form = GroupEditForm()
    if form_data != {}:
        form_data["nextcloud_groupfolder"] = unix.nextcloud_groupfolder_exists(cn)
        form = GroupEditForm(form_data)
    return render(request, "idm/admin/edit_group.html", {"form": form, "message": message, "cn": cn})

@staff_member_required(login_url=settings.LOGIN_URL)
def delete_group(request, cn):
    ldap_delete_group(cn)
    return redirect(group_overview)

@staff_member_required(login_url=settings.LOGIN_URL)
def assign_users_to_group(request, cn):
    users = ldap_get_all_users()
    group_dn = ldap_get_group_information_of_cn(cn)["dn"]
    message = ""
    for user in users:
        user["memberOfCurrentGroup"] = is_user_in_group(user, cn)
    if request.method == 'POST':
        for user in users:
            # Add user to group
            if request.POST.get(user["cn"], "") == "On" and not is_user_in_group(user, cn):
                print("Add user " + user["cn"] + " to group " + cn)
                message = ldap_add_user_to_group(user["dn"], group_dn)
                user["memberOfCurrentGroup"] = True
            # Remove user from group
            elif request.POST.get(user["cn"], "") == "" and is_user_in_group(user, cn):
                print("Remove user " + user["cn"] + " from group " + cn)
                message = ldap_remove_user_from_group(user["dn"], group_dn)
                user["memberOfCurrentGroup"] = False
        if message == None or message == "":
            message = "Mitgliedschaften erfolgreich aktualisiert!"
    
    if request.method == 'GET':
        if request.GET.get("select_all", "") != "":
            for user in users:
                if not is_user_in_group(user, cn):
                    message = ldap_add_user_to_group(user["dn"], group_dn)
                    user["memberOfCurrentGroup"] = True
            return redirect(assign_users_to_group, cn=cn)
        if request.GET.get("deselect_all", "") != "":
            for user in users:
                if is_user_in_group(user, cn):
                    message = ldap_remove_user_from_group(user["dn"], group_dn)
                    user["memberOfCurrentGroup"] = False
            return redirect(assign_users_to_group, cn=cn)

        

    return render(request, "idm/admin/assign_users_to_group.html", {"users": users, "cn": cn, "message": message})


@staff_member_required(login_url=settings.LOGIN_URL)
def assign_groups_to_user(request, cn):
    groups = ldap_get_all_groups()
    user_information = get_user_information_of_cn(cn)
    message = ""
    for user_group in user_information["groups"]:
        for group in groups:
            if group["dn"].lower() == user_group.lower():
                group["memberOfCurrentUser"] = True
    if request.method == 'POST':
        for group in groups:
            # Add user to group
            if request.POST.get(group["cn"], "") == "On" and not group.get("memberOfCurrentUser", False):
                print("Add user " + cn + " to group " + group["cn"])
                message = ldap_add_user_to_group(user_information["dn"], group["dn"])
                group["memberOfCurrentUser"] = True
            # Remove user from group
            elif request.POST.get(group["cn"], "") == "" and group.get("memberOfCurrentUser", False):
                print("Remove user " + cn + " from group " + group["cn"])
                message = ldap_remove_user_from_group(user_information["dn"], group["dn"])
                group["memberOfCurrentUser"] = False
        if message == None or message == "":
            message = "Mitgliedschaften erfolgreich aktualisiert!"
        return render(request, "idm/admin/assign_groups_to_user.html", {"groups": groups, "user_information": user_information, "message": message})
    
    return render(request, "idm/admin/assign_groups_to_user.html", {"groups": groups, "user_information": user_information, "message": message})
    
@staff_member_required(login_url=settings.LOGIN_URL)
def oidc_client_overview(request):
    discovery_url = request.build_absolute_uri(reverse("oidc_provider:provider-info"))
    overview = templates.process_overview_dict({
        "heading": "OIDC Clients",
        "element_name": "OIDC Client",
        "element_url_key": "id",
        "elements": Client.objects.all(),
        "t_headings": ["Name"],
        "t_keys": ["name"],
        "add_url_name": "create_oidc_client",
        "edit_url_name": "edit_oidc_client",
        "delete_url_name": "delete_oidc_client",
        "hint": "OpenID Connect Discovery URL: <a href='" + discovery_url + "'>" + discovery_url + "</a>",
    })
    return render(request, "lac/overview_x.html", {"overview": overview})

@staff_member_required(login_url=settings.LOGIN_URL)
def create_oidc_client(request):
    form = OIDCClientForm()
    if request.method == 'POST':
        form = OIDCClientForm(request.POST)
        if form.is_valid():
            add_oidc_provider_client(form.cleaned_data)
            return redirect(oidc_client_overview)
    # Get random id and secret
    client_id = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))
    client_secret = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=32))
    form.fields["client_id"].initial = client_id
    form.fields["client_secret"].initial = client_secret
    return render(request, "lac/create_x.html", {"form": form, "url": reverse("oidc_client_overview")})


@staff_member_required(login_url=settings.LOGIN_URL)
def edit_oidc_client(request, id):
    client = Client.objects.get(id=id)
    print(client.response_types.all())
    form = OIDCClientForm(initial={
        "name": client.name,
        "client_type": client.client_type,
        "response_types": client.response_types.all(),
        "redirect_uris": "\n".join(client.redirect_uris),
        "client_id": client.client_id,
        "client_secret": client.client_secret,
        "jwt_alg": client.jwt_alg,
        "require_consent": client.require_consent,
        "reuse_consent": client.reuse_consent,
    })
    if request.method == 'POST':
        form = OIDCClientForm(request.POST)
        if form.is_valid():
            client.name = form.cleaned_data["name"]
            client.client_type = form.cleaned_data["client_type"]
            client.response_types.set(form.cleaned_data["response_types"])
            client.redirect_uris = form.cleaned_data["redirect_uris"].split("\n")
            client.client_id = form.cleaned_data["client_id"]
            client.client_secret = form.cleaned_data["client_secret"]
            client.jwt_alg = form.cleaned_data["jwt_alg"]
            client.require_consent = form.cleaned_data["require_consent"]
            client.reuse_consent = form.cleaned_data["reuse_consent"]
            client.save()
            return redirect(oidc_client_overview)
    return render(request, "lac/edit_x.html", {"form": form, "id": id, "url": reverse("oidc_client_overview")})

@staff_member_required(login_url=settings.LOGIN_URL)
def delete_oidc_client(request, id):
    client = Client.objects.get(id=id)
    client.delete()
    return redirect(oidc_client_overview)


@staff_member_required(login_url=settings.LOGIN_URL)
def api_key_overview(request):
    api_keys = ApiKey.objects.filter(user=request.user).order_by("-created_at")
    overview_dict = templates.process_overview_dict({
        "heading": "API Keys",
        "element_name": "API Key",
        "element_url_key": "id",
        "elements": api_keys,
        "t_headings": ["Name", "Created At", "Last Used At", "Expiration Date"],
        "t_keys": ["name", "created_at", "last_used_at", "expiration_date"],
        "add_url_name": "create_api_key",
        "edit_url_name": "edit_api_key",
        "delete_url_name": "delete_api_key",
        "info_url_name": "api_key_details",
        "hint": "You can view all api endpoints <a href='/api/schema/swagger-ui/' target='_blank'>here</a>.",
    })
    return render(request, "lac/overview_x.html", {"overview": overview_dict})


@staff_member_required(login_url=settings.LOGIN_URL)
def create_api_key(request):
    form = ApiKeyForm()
    if request.method == 'POST':
        form = ApiKeyForm(request.POST)
        if form.is_valid():
            api_key = ApiKey()
            api_key.user = request.user
            api_key.name = form.cleaned_data["name"]
            api_key.key = generate_random_password(length=64, alphanumeric_only=True)  # Generate a random key
            api_key.expiration_date = form.cleaned_data["expiration_date"]
            api_key.save()
            return redirect(api_key_overview)
    form.fields["expiration_date"].initial = datetime.datetime.now() + datetime.timedelta(days=365)  # Default to 1 year
    return render(request, "lac/create_x.html", {"form": form, "url": reverse("api_key_overview"), "hide_buttons_top": True})


@staff_member_required(login_url=settings.LOGIN_URL)
def edit_api_key(request, id):
    # Check if the user is the owner of the API key
    if not ApiKey.objects.filter(id=id, user=request.user).exists():
        return lac.templates.message(request, "Sie sind nicht berechtigt, diesen API-Schlüssel zu bearbeiten!", "api_key_overview")
    api_key = ApiKey.objects.get(id=id)
    form = ApiKeyForm(initial={
        "name": api_key.name,
        "expiration_date": api_key.expiration_date,
    })
    if request.method == 'POST':
        form = ApiKeyForm(request.POST)
        if form.is_valid():
            api_key.name = form.cleaned_data["name"]
            api_key.expiration_date = form.cleaned_data["expiration_date"]
            api_key.save()
            return redirect(api_key_overview)
    return render(request, "lac/edit_x.html", {"form": form, "id": id, "url": reverse("api_key_overview")})


@staff_member_required(login_url=settings.LOGIN_URL)
def delete_api_key(request, id):
    # Check if the user is the owner of the API key
    if not ApiKey.objects.filter(id=id, user=request.user).exists():
        return lac.templates.message(request, "Sie sind nicht berechtigt, diesen API-Schlüssel zu löschen!", "api_key_overview")
    api_key = ApiKey.objects.get(id=id)
    api_key.delete()
    return redirect(api_key_overview)


@staff_member_required(login_url=settings.LOGIN_URL)
def api_key_details(request, id):
    # Check if the user is the owner of the API key
    if not ApiKey.objects.filter(id=id, user=request.user).exists():
        return lac.templates.message(request, "Sie sind nicht berechtigt, diese API-Schlüssel-Details anzuzeigen!", "api_key_overview")
    api_key = ApiKey.objects.get(id=id)
    return lac.templates.message(request, f"API Key Details:<br>Name: {api_key.name}<br>Key: {api_key.key}<br>Created At: {api_key.created_at}<br>Last Used At: {api_key.last_used_at}<br>Expiration Date: {api_key.expiration_date}", "api_key_overview")



class UserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Returns a list of all users.
        """
        users = ldap_get_all_users()
        serializer = UserSerializer(users, many=True)
        return HttpResponse(JSONRenderer().render(serializer.data), content_type="application/json")

    def retrieve(self, request, pk=None):
        """
        Returns the user information for a specific user identified by `user`.
        """
        user_info = get_user_information_of_cn(pk)
        if not user_info:
            return HttpResponse(status=404)
        serializer = UserSerializer(user_info)
        return HttpResponse(JSONRenderer().render(serializer.data), content_type="application/json")
    
    @action(detail=True, methods=['post'], url_name='enable')
    def enable(self, request, pk=None):
        """
        Enables a user identified by `user`.
        """
        msg = ldap_enable_user(pk)
        if msg:
            return HttpResponse("Failed to enable user." + msg, status=500)
        return HttpResponse(f"User {pk} has been successfully enabled.", status=200)
    
    @action(detail=True, methods=['post'], url_name='disable')
    def disable(self, request, pk=None):
        """
        Disables a user identified by its username.
        """
        msg = ldap_disable_user(pk)
        if msg:
            return HttpResponse("Failed to disable user." + msg, status=500)
        return HttpResponse(f"User {pk} has been successfully disabled.", status=200)

    
    @action(detail=True, methods=['post'], url_name='reset_2fa')
    def reset_2fa(self, request, pk=None):
        """
        Resets all 2FA for a user identified by its username.
        """
        msg = idm.idm.reset_2fa_for_username(pk)
        if msg:
            return HttpResponse("Failed to reset 2FA for user. " + msg, status=500)
        return HttpResponse(f"2FA for user {pk} has been successfully reset.", status=200)
    
    @action(detail=True, methods=['post'], url_name='set_password')
    def set_password(self, request, pk=None):
        """
        Set the password for a user identified by its username.
        
        ---
        Data fields:
        - new_password: The new password to set for the user. Must be at least 8 characters long.
        """
        new_password = request.data.get("new_password", "")
        print(f"Setting new password for user {pk}: {new_password}")
        if len(new_password) > 7:
            msg = set_user_new_password(pk, new_password)
            if msg:
                return HttpResponse(msg, status=400)
            return HttpResponse(f"Password for user {pk} has been successfully changed.", status=200)

        else:
            return HttpResponse("Password too short.", status=400)
        
    def destroy(self, request, pk=None):
        """
        Deletes a user identified by its username.
        """
        msg = ldap_delete_user(pk)
        if msg:
            print(f"Failed to delete user {pk}: {msg}")
            return HttpResponse("Failed to delete user. " + msg, status=500)
        unix.desktop_remove_user(pk)
        return HttpResponse(f"User {pk} has been successfully deleted.", status=200)
    
    def update(self, request, pk=None):
        """
        Updates the user information for a specific user identified by `user`.

        ---
        Data fields:
        - display_name: The display name of the user.
        - first_name: The first name of the user
        - last_name: The last name of the user
        - mail: The email address of the user.
        - admin: Boolean indicating if the user is an administrator.
        - enabled: Boolean indicating if the user is enabled.
        - password: The new password for the user (optional, if not provided, the password will not be changed).
        """
        
        user_information = request.data
        user_information["username"] = pk  # Ensure the username is set to the user
        user_information["displayName"] = user_information.get("display_name", "")
           
        msg = ldap_update_user(pk, user_information)
        if msg:
            return HttpResponse(msg, status=400)
        return HttpResponse(f"User {pk} has been successfully updated.", status=200)

        
    def create(self, request):
        """
        Creates a new user with the information provided in the request body.
        ---
        Data fields:
        - username: The username for the new user.
        - first_name: The first name of the user.
        - last_name: The last name of the user.
        - mail: The email address of the user.
        - admin: Boolean indicating if the user is an administrator.
        - password: The password for the new user.
        """
        user_information = request.data

        msg = ldap_create_user(user_information)
        if msg:
            return HttpResponse(msg, status=400)
        username = user_information.get("username", "")
        unix.desktop_add_user(username, "", user_information.get("admin", False))
        return HttpResponse(f"User {username} has been successfully created.", status=201)
        


class GroupViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Returns a list of all groups.
        """
        groups = ldap_get_all_groups()
        serializer = GroupSerializer(groups, many=True)
        return HttpResponse(JSONRenderer().render(serializer.data), content_type="application/json")

    def retrieve(self, request, pk=None):
        """
        Returns the group information for a specific group identified by `group`.
        """
        group_info = ldap_get_group_information_of_cn(pk)
        if not group_info:
            return HttpResponse(status=404)
        serializer = GroupSerializer(group_info)
        return HttpResponse(JSONRenderer().render(serializer.data), content_type="application/json")
    
    def create(self, request):
        """
        Creates a new group with the information provided in the request body.
        ---
        Data fields:
        - name: The common name for the new group.
        - description: A description of the group.
        - default: Boolean indicating if this group should be a default group.
        """
        group_information = request.data

        group_information["cn"] = group_information.get("name", "")
        group_information["defaultGroup"] = group_information.get("default", False)

        msg = ldap_create_group(group_information)
        if msg:
            return HttpResponse(msg, status=400)

        return HttpResponse(f"Group {group_information['cn']} has been successfully created.", status=201)
    

    def update(self, request, pk=None):
        """
        Updates the group information for a specific group identified by `group`.

        ---
        Data fields:
        - name: The common name for the group.
        - description: A description of the group.
        - default: Boolean indicating if this group should be a default group.
        """
        group_information = request.data
        group_information["cn"] = pk
        group_information["defaultGroup"] = group_information.get("default", False)
        msg = ldap_update_group(pk, group_information)
        if msg:
            return HttpResponse(msg, status=400)
       
        return HttpResponse(f"Group {pk} has been successfully updated.", status=200)
    
    def destroy(self, request, pk=None):
        """
        Deletes a group identified by its common name `group`.
        """
        msg = ldap_delete_group(pk)
        if msg:
            return HttpResponse("Failed to delete group. " + msg, status=500)
        return HttpResponse(f"Group {pk} has been successfully deleted.", status=200)