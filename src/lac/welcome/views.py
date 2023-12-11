from django.shortcuts import render, redirect
import os
import subprocess
from django.conf import settings

subdomains = ["cloud", "office", "portal", "central", "la", "chat", "meet"]

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

    return render(request, "welcome/welcome_start.html", {"message": message})


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

    return render(request, "welcome/welcome_select_apps.html")


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
            return redirect("welcome_email_settings")
    return render(request, "welcome/welcome_dns_settings.html", {"message": message, "subdomains": subdomains})


def welcome_email_settings(request):
    if request.method == "POST":
        request.session["mailhost"] = request.POST.get("mailhost", "")
        request.session["mailport"] = request.POST.get("mailport", "")
        request.session["mailuser"] = request.POST.get("mailuser", "")
        request.session["mailpassword"] = request.POST.get("mailpassword", "")
        request.session["mailencryption"] = request.POST.get("mailencryption", " ")
        ## TODO: Start here the installation process
        return redirect("installation_running")
    return render(request, "welcome/welcome_email_settings.html", {"message": ""})


def installation_running(request):
    message = ""
    os.environ["DOMAIN"] = request.session["domain"]
    os.environ["ADMIN_PASSWORD"] = request.session["password"]
    # Get output of script: in lac/welcome/scripts/get_ip.sh
    os.environ["IP"] = os.popen("hostname -I").read().split(" ")[0]
    os.environ["EMAIL_HOST"] = request.session["mailhost"]
    os.environ["EMAIL_PORT"] = request.session["mailport"]
    os.environ["EMAIL_HOST_USER"] = request.session["mailuser"]
    os.environ["EMAIL_HOST_PASSWORD"] = request.session["mailpassword"]
    os.environ["MAIL_ENCRYPTION"] = request.session["mailencryption"]
    # Run basics script
    os.environ["NEXTCLOUD"] = request.session["nextcloud"]
    os.environ["ONLYOFFICE"] = request.session["onlyoffice"]
    os.environ["COLLABORA"] = request.session["collabora"]
    os.environ["ROCKETCHAT"] = request.session["rocketchat"]
    os.environ["JITSI"] = request.session["jitsi"]

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
    }

    # Create rendered access_rendered.html
    with open(f'{settings.BASE_DIR}/welcome/templates/welcome/access_rendered.html', 'w') as f:
        string = render(request, "welcome/access.html", variables).content.decode("utf-8")
        string = "{% extends \"lac/base.html\" %}\n{% block content %}\n" + string + "\n{% endblock %}"
        f.write(string)

    variables["installation_running"] = True
    return render(request, "welcome/installation_running.html", variables)


def access(request):
    return render(request, "welcome/access_rendered.html")