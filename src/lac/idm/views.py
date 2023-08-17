from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
import django_auth_ldap.backend
from django_auth_ldap.backend import LDAPBackend
from .forms import BasicUserForm, PasswordForm, PasswordResetForm
from .ldap import get_user_information_of_ldap, update_user_information_ldap, is_ldap_user_password_correct, set_ldap_user_new_password
from .idm import reset_password_for_email
from django.contrib.auth.decorators import login_required
import time

def signal_handler(context, user, request, exception, **kwargs):
    print("Context: " + str(context) + "\nUser: " + str(user) + "\nRequest: " + str(request) + "\nException: " + str(exception))

django_auth_ldap.backend.ldap_error.connect(signal_handler)





# Create your views here.
def index(request):
    if request.user.is_authenticated:
        user_information = get_user_information_of_ldap(request.user.ldap_user)       
        return render(request, "idm/index.html", {"request": request, "user_information": user_information})
    return redirect(user_login)

def user_login(request):
    if request.user.is_authenticated:
        return redirect(index)
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user and user.is_authenticated:
            print("User is authenticated")
            login(request, user)
            # if request.GET.get("next", "") != "":
            #     return HttpResponseRedirect(request.GET['next'])
            # else: 
            return redirect(index)
        else:
            print("User is not authenticated")
            return render(request, 'idm/login.html', {'error_message': "Anmeldung fehlgeschlagen! Bitte versuchen Sie es erneut."})
    return render(request, "idm/login.html", {"request": request})

def user_logout(request):
    logout(request)
    return redirect(index)

@login_required
def user_settings(request):
    
    if request.method == 'POST':
        form = BasicUserForm(request.POST)
        if form.is_valid():
            update_user_information_ldap(request.user.ldap_user, form.cleaned_data)
        form.cleaned_data.update({"username": request.user.username})
        print(form.cleaned_data)
        form = BasicUserForm(initial=form.cleaned_data)
        return render(request, "idm/user_settings.html", {"form": form})

    else:
        user_information = get_user_information_of_ldap(request.user.ldap_user)
        form = BasicUserForm(initial=user_information)
        return render(request, "idm/user_settings.html", {"form": form})    


def user_password_reset(request):
    message = ""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            reset_password_for_email(form.cleaned_data["email"])
            print("HUHU")
            message = "Sollte die E-Mail-Adresse in unserem System existieren, wurde eine E-Mail mit einem Link zum Zurücksetzen des Passworts versendet."
        else:
            message = "Bitte geben Sie eine gültige E-Mail-Adresse ein."
    form = PasswordResetForm()
    return render(request, "idm/reset_password.html", {"form": form, "message": message})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        form_valid = False
        message = ""
        if form.is_valid():
            if form.cleaned_data["new_password"] == form.cleaned_data["new_password_repeat"]:
                if is_ldap_user_password_correct(request.user.ldap_user.dn, form.cleaned_data["old_password"]):
                    set_ldap_user_new_password(request.user.ldap_user.dn, form.cleaned_data["new_password"])
                    message = "Das Passwort wurde erfolgreich geändert!"
                else:
                    message = "Das alte Passwort ist nicht korrekt!"
            else:
                message = "Die neuen Passwörter stimmen nicht überein!"
        return render(request, "idm/change_password.html", {"form": form, "message": message})
    else:
        form = PasswordForm()
        return render(request, "idm/change_password.html", {"form": form})


def user_administration_overview(request):
    return render(request, "idm/user_administration_overview.html")