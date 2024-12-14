from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
import django_auth_ldap.backend
from django_auth_ldap.backend import LDAPBackend
from .forms import BasicUserForm, PasswordForm, PasswordResetForm, AdministratorUserForm, AdministratorUserEditForm, GroupCreateForm, GroupEditForm, OIDCClientForm, TOTPChallengeForm
from .ldap import get_user_information_of_cn, is_ldap_user_password_correct, set_ldap_user_new_password, ldap_get_all_users, ldap_create_user, ldap_update_user, ldap_delete_user, ldap_get_all_groups, ldap_create_group, ldap_update_group, ldap_get_group_information_of_cn, ldap_delete_group, is_user_in_group, ldap_remove_user_from_group, ldap_add_user_to_group, get_user_dn_by_email, ldap_get_cn_of_dn
from .idm import reset_password_for_email, get_user_information, set_user_new_password, is_user_password_correct
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


def signal_handler(context, user, request, exception, **kwargs):
    print("Context: " + str(context) + "\nUser: " + str(user) + "\nRequest: " + str(request) + "\nException: " + str(exception))

django_auth_ldap.backend.ldap_error.connect(signal_handler)


# Create your views here.
@login_required
def dashboard(request):
    user_information = get_user_information(request.user)
    challenges = idm.challenges.get_all_libre_workspace_challenges(request.user)
    # Only take the last three challenges because we don't want to overwhelm the user
    if len(challenges) > 3:
        challenges = challenges[-3:]
    return render(request, "idm/dashboard.html", {"request": request, "user_information": user_information, "ldap_enabled": settings.AUTH_LDAP_ENABLED, "challenges": challenges})


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
            if device.verify_token(request.POST.get("token", "")):
                print("TOTP code is correct")
                login(request, user)
                if request.GET.get("next", "") != "":
                    return HttpResponseRedirect(request.GET['next'])
                else: 
                    return redirect("index")
            else:
                print("TOTP code is not correct: " + request.POST.get("token", ""))
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

@login_required
def get_totp_challenge_site(request, user, message=""):
    # Check if user has totp enabled
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

    # Generate QR code with qrcode module
    img = qrcode.make(url)
    img.save(settings.MEDIA_ROOT + f"/totp_{device.id}.png")

    base32_code = str(b32encode(device.bin_key))[2:-1]

    return render(request, "idm/add_new_totp_device.html", {"base32_code": base32_code, "img": settings.MEDIA_URL + f"totp_{device.id}.png", "device_name": device.name})

    pass

@login_required
def delete_totp_device(request, id):
    device = TOTPDevice.objects.get(id=id)
    device.delete()
    # Also remove all totp_*.png files
    import os
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
                if user_information.get("create_linux_user", False):
                    print(user_information)
                    message = unix.create_linux_user(user_information["username"], str(user_information["first_name"]) + " " +  str(user_information["last_name"]), user_information["password"], user_information.get("admin", False))
                    # Reset form even if an error occured on linux side because the ldap user was created successfully
                    form = AdministratorUserForm()
            if message == None:
                username = user_information.get("username", "")
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
    print(unix.delete_linux_user(cn))
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
    })
    return render(request, "lac/overview_x.html", {"overview": overview})

@staff_member_required(login_url=settings.LOGIN_URL)
def create_oidc_client(request):
    form = OIDCClientForm()
    if request.method == 'POST':
        form = OIDCClientForm(request.POST)
        if form.is_valid():
            print("342")
            print(form.cleaned_data["response_types"])
            client = Client()
            client.name = form.cleaned_data["name"]
            client.client_type = form.cleaned_data["client_type"]
            client.redirect_uris = form.cleaned_data["redirect_uris"].split("\n")
            client.client_id = form.cleaned_data["client_id"]
            client.client_secret = form.cleaned_data["client_secret"]
            client.jwt_alg = form.cleaned_data["jwt_alg"]
            client.require_consent = form.cleaned_data["require_consent"]
            client.reuse_consent = form.cleaned_data["reuse_consent"]
            client.save()
            client.response_types.set(form.cleaned_data["response_types"])
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