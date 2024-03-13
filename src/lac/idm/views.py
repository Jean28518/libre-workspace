from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
import django_auth_ldap.backend
from django_auth_ldap.backend import LDAPBackend
from .forms import BasicUserForm, PasswordForm, PasswordResetForm, AdministratorUserForm, AdministratorUserEditForm, GroupCreateForm, GroupEditForm
from .ldap import get_user_information_of_cn, is_ldap_user_password_correct, set_ldap_user_new_password, ldap_get_all_users, ldap_create_user, ldap_update_user, ldap_delete_user, ldap_get_all_groups, ldap_create_group, ldap_update_group, ldap_get_group_information_of_cn, ldap_delete_group, is_user_in_group, ldap_remove_user_from_group, ldap_add_user_to_group, get_user_dn_by_email, ldap_get_cn_of_dn
from .idm import reset_password_for_email, get_user_information, set_user_new_password, is_user_password_correct
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import idm.challenges


def signal_handler(context, user, request, exception, **kwargs):
    print("Context: " + str(context) + "\nUser: " + str(user) + "\nRequest: " + str(request) + "\nException: " + str(exception))

django_auth_ldap.backend.ldap_error.connect(signal_handler)


# Create your views here.
@login_required
def dashboard(request):
    user_information = get_user_information(request.user)
    challenges = idm.challenges.get_all_libre_workspace_challenges()
    # Only take the last three challenges because we don't want to overwhelm the user
    if len(challenges) > 3:
        challenges = challenges[-3:]
    return render(request, "idm/dashboard.html", {"request": request, "user_information": user_information, "ldap_enabled": settings.AUTH_LDAP_ENABLED, "challenges": challenges})


# We have to set login_page=True to prevent the base template from displaying the login button
def user_login(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == 'POST':
        username = request.POST['username']

        # Check if user entered email address, if so, convert to username
        if "@" in username and "." in username:
            userdn = get_user_dn_by_email(username)
            if userdn == None:
                return render(request, 'idm/login.html', {'error_message': "Anmeldung fehlgeschlagen! Bitte versuchen Sie es mit Ihrem Nutzernamen.", "login_page": True})
            username = ldap_get_cn_of_dn(userdn)

        user = authenticate(username=username, password=request.POST['password'])
        if user and user.is_authenticated:
            print("User is authenticated")
            login(request, user)
            if request.GET.get("next", "") != "":
                return HttpResponseRedirect(request.GET['next'])
            else: 
                return redirect("index")
        else:
            print("User is not authenticated")
            return render(request, 'idm/login.html', {'error_message': "Anmeldung fehlgeschlagen! Bitte versuchen Sie es erneut.", "login_page": True})
    return render(request, "idm/login.html", {"request": request, "hide_login_button": True})


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


@login_required
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
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        message = ""
        if form.is_valid():
            if form.cleaned_data["new_password"] == form.cleaned_data["new_password_repeat"]:
                if is_user_password_correct(request.user, form.cleaned_data["old_password"]):
                    message = set_user_new_password(request.user, form.cleaned_data["new_password"])
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
    form_data = {}
    print(request)
    if request.method == 'POST':
        form = AdministratorUserForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            user_information = form.cleaned_data
            message = ldap_create_user(user_information)
            if message == None:
                username = user_information.get("username", "")
                message = f"Benutzer '{username}' erfolgreich erstellt!"
        else:
            print("Form is not valid")
            print(form.errors)
            message = form.errors
            form_data = form.cleaned_data

    form = AdministratorUserForm()
    if form_data != {}:
        form = AdministratorUserForm(form_data)
    return render(request, "idm/admin/create_user.html", {"form": form, "message": message})

    
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
    return render(request, "idm/admin/edit_user.html", {"form": form, "message": message, "cn": cn})#

@staff_member_required(login_url=settings.LOGIN_URL)
def delete_user(request, cn):
    ldap_delete_user(cn)
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
            if message == None:
                message = f"Änderungen erfolgreich gespeichert!"
        else:
            message = form.errors
        form_data = form.cleaned_data
    form = GroupEditForm()
    if form_data != {}:
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
    
