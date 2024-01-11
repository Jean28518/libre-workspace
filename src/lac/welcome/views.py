from django.shortcuts import render, redirect
import os
import subprocess
from django.conf import settings
from .forms import EmailConfiguration

import welcome.cfg as cfg

import welcome.scripts.update_email_settings as update_email_settings

subdomains = ["cloud", "office", "portal", "la", "chat", "meet"]

# Create your views here.
def welcome_start(request):
    # If request is POST
    message = ""
    if request.method == "POST":
        password = request.POST["password"]
        password_repeat = request.POST["password_repeat"]
        if password.strip() == "":
            message = "Passwort darf nicht leer sein."
        if password.count(" ") > 0:
            message = "Passwort darf keine Leerzeichen enthalten."
        # Check if password contains at least one number
        if not any(char.isdigit() for char in password):
            message = "Passwort muss mindestens eine Zahl enthalten."
        # Check if password contains at least one letter
        if not any(char.isalpha() for char in password):
            message = "Passwort muss mindestens einen Buchstaben enthalten."
        # Check if password contains at least one special character
        special_characters = "!\"%&'()*+,-./:;<=>?@[\]^_`{|}~"
        if not any(char in special_characters for char in password):
            message = "Passwort muss mindestens ein Sonderzeichen enthalten."
        # If password contains "$'# it is forbidden
        forbidden_characters = "$'#"
        if any(char in forbidden_characters for char in password):
            message = "Passwort darf keine der folgenden Zeichen enthalten: $'#"
        # Check if password is at least 8 characters long
        if len(password) < 8:
            message = "Passwort muss mindestens 8 Zeichen lang sein."
        if password == password_repeat:
            request.session["password"] = password
        else:
            message = "Passwörter stimmen nicht überein. Bitte versuchen Sie es erneut."
        if message == "":
            return redirect("welcome_select_apps")

    return render(request, "welcome/welcome_start.html", {"message": message, "hide_login_button": True})


def welcome_select_apps(request):
    if request.method == "POST":
        request.session["nextcloud"] = request.POST.get("nextcloud", "")
        if request.POST.get("online_office", "") == "onlyoffice":
            request.session["onlyoffice"] = "onlyoffice"
            request.session["collabora"] = ""
        elif request.POST.get("online_office", "") == "collabora":
            request.session["collabora"] = "collabora"
            request.session["onlyoffice"] = ""
        else:
            request.session["onlyoffice"] = ""
            request.session["collabora"] = ""
        request.session["rocketchat"] = request.POST.get("rocketchat", "")
        request.session["jitsi"] = request.POST.get("jitsi", "")
        return redirect("welcome_dns_settings")

    return render(request, "welcome/welcome_select_apps.html", {"hide_login_button": True})


def welcome_dns_settings(request):
    message = ""
    if request.method == "POST":
        request.session["visibility"] = request.POST.get("visibility", "")
        request.session["domain"] = request.POST.get("domain", "")
        if request.session["visibility"] == "public":
            if request.session["domain"] == "":
                message = "Bitte geben Sie eine Domain an."
            elif request.session["domain"].count(".") != 1:
                message = "Bitte stellen Sie sicher, dass Sie nur die Domain angeben und keine Subdomain."
        else:
            request.session["domain"] = "int.de"
        if message == "":
            return redirect("installation_running")
    return render(request, "welcome/welcome_dns_settings.html", {"message": message, "subdomains": subdomains, "hide_login_button": True})


def installation_running(request):
    message = ""
    os.environ["DOMAIN"] = request.session["domain"]
    os.environ["ADMIN_PASSWORD"] = request.session["password"]
    # Get output of script: in lac/welcome/scripts/get_ip.sh
    os.environ["IP"] = os.popen("hostname -I").read().split(" ")[0]
    # Run basics script
    os.environ["NEXTCLOUD"] = request.session["nextcloud"]
    os.environ["ONLYOFFICE"] = request.session["onlyoffice"]
    os.environ["COLLABORA"] = request.session["collabora"]
    os.environ["ROCKETCHAT"] = request.session["rocketchat"]
    os.environ["JITSI"] = request.session["jitsi"]

    # Create env.sh file
    with open("/usr/share/linux-arbeitsplatz/welcome/scripts/env.sh", "w") as f:
        f.write(f"export DOMAIN={os.environ['DOMAIN']}\n")
        f.write(f"export IP={os.environ['IP']}\n")
        f.write(f"export ADMIN_PASSWORD={os.environ['ADMIN_PASSWORD']}\n")

    # Run installation script
    # if file /usr/share/linux-arbeitsplatz/welcome/scripts/installation_running exists
    if not os.path.isfile("/usr/share/linux-arbeitsplatz/welcome/scripts/installation_running"):
        if os.path.isfile("/usr/share/linux-arbeitsplatz/welcome/scripts/install.sh"):
            subprocess.Popen(["/usr/bin/bash", "/usr/share/linux-arbeitsplatz/welcome/scripts/install.sh"], cwd="/usr/share/linux-arbeitsplatz/welcome/scripts/" )
        else:
            print("WARNING: Installation script not found! If you are in a development environment, thats okay. If you are in a production environment, please check your installation.")
            message = "WARNING: Installation script not found! If you are in a development environment, thats okay. If you are in a production environment, please check your installation."
    
    if not "cert" in subdomains:
        subdomains.append("cert")

    variables = {
        "message": message, 
        "subdomains": subdomains, 
        "domain": os.environ["DOMAIN"],
        "ip": os.environ["IP"],
        "hide_login_button": True,
    }

    # Create rendered access_rendered.html
    with open(f'{settings.BASE_DIR}/welcome/templates/welcome/access_rendered.html', 'w') as f:
        string = render(request, "welcome/access.html", variables).content.decode("utf-8")
        string = "{% extends \"lac/base.html\" %}\n{% block content %}\n" + string + "\n{% endblock %}"
        f.write(string)

    variables["installation_running"] = True
    return render(request, "welcome/installation_running.html", variables)


def access(request):
    return render(request, "welcome/access_rendered.html", {"hide_login_button": True})


def system_configuration(request):
    return render(request, "welcome/system_configuration.html", {"hide_login_button": True})


# Thats the config dashboard in system configuration
def email_configuration(request):
    message = ""
    current_email_conf = {
        "server": cfg.get_value("EMAIL_HOST", ""),
        "port": cfg.get_value("EMAIL_PORT", ""),
        "user": cfg.get_value("EMAIL_HOST_USER", ""),
        "password": cfg.get_value("EMAIL_HOST_PASSWORD", ""),       
    }
    if cfg.get_value("EMAIL_USE_TLS", "False") == "True":
        current_email_conf["encryption"] = "TLS"
    else:
        current_email_conf["encryption"] = "SSL"
    form = EmailConfiguration(request.POST or None, initial=current_email_conf)

    if request.method == "POST":
        form = EmailConfiguration(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            cfg.set_value("EMAIL_HOST", form.cleaned_data["server"])
            cfg.set_value("EMAIL_PORT", form.cleaned_data["port"])
            cfg.set_value("EMAIL_HOST_USER", form.cleaned_data["user"])
            if form.cleaned_data["password"] != "":
                cfg.set_value("EMAIL_HOST_PASSWORD", form.cleaned_data["password"])
            if form.cleaned_data["encryption"] == "TLS":
                cfg.set_value("EMAIL_USE_TLS", "True")
                cfg.set_value("EMAIL_USE_SSL", "False")
            else:
                cfg.set_value("EMAIL_USE_TLS", "False")
                cfg.set_value("EMAIL_USE_SSL", "True")
            message = "E-Mail Konfiguration gespeichert."
            mail_config = form.cleaned_data.copy()
            if (mail_config["password"] == ""):
                mail_config["password"] = current_email_conf["password"]
            update_email_settings.update_email_settings(form.cleaned_data)

    return render(request, "welcome/email_configuration.html", {"current_email_conf": current_email_conf, "form": form, "message": message})