from django.shortcuts import render, redirect
import os
import subprocess
from django.conf import settings
import unix.unix_scripts.unix as unix
from django.http import HttpResponse
from lac.templates import message as message_func


# List of subdomains
subdomains = ["cloud", "office", "portal", "la", "chat", "meet", "element", "matrix"]

# Create your views here.
def welcome_start(request):
    # If request is POST
    message = ""
    if request.method == "POST":
        password = request.POST["password"]
        password_repeat = request.POST["password_repeat"]
        message = unix.password_challenge(password)
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
        # Don't install onlyoffice or collabora if nextcloud is not installed
        if not request.session["nextcloud"]:
            request.session["onlyoffice"] = ""
            request.session["collabora"] = ""
        request.session["matrix"] = request.POST.get("matrix", "")
        request.session["jitsi"] = request.POST.get("jitsi", "")
        request.session["xfce"] = request.POST.get("xfce", "")
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
            lvl1 = request.session["domain"].split(".")[1]
            if len(lvl1) > 12:
                message = "Bitte stellen Sie sicher, dass die lvl1 Domain nicht länger als 12 Zeichen ist."
            lvl2 = request.session["domain"].split(".")[0]
            # We need the -1 because of the dot
            shortend_lvl2 = lvl2[:12-len(lvl1)-1]
            request.session["ldap_dc"] = f"dc={shortend_lvl2},dc={lvl1}"
        else:
            request.session["domain"] = "int.de"
            request.session["ldap_dc"] = "dc=int,dc=de"
        if message == "":
            return redirect("installation_running")
    return render(request, "welcome/welcome_dns_settings.html", {"message": message, "subdomains": subdomains, "hide_login_button": True})


def installation_running(request):
    if os.environ["LINUX_ARBEITSPLATZ_CONFIGURED"] == "True":
        return message_func(request, "Libre Workspace ist bereits konfiguriert. Bitte loggen Sie sich ein.")
    message = ""
    os.environ["DOMAIN"] = request.session["domain"]
    os.environ["ADMIN_PASSWORD"] = request.session["password"]
    # Get output of script: in lac/unix/unix_scripts/get_ip.sh
    os.environ["IP"] = os.popen("hostname -I").read().split(" ")[0]
    os.environ["LDAP_DC"] = request.session["ldap_dc"]
    # Run basics script
    os.environ["SAMBA_DC"] = request.session["nextcloud"] or request.session["matrix"] or request.session["jitsi"]
    os.environ["NEXTCLOUD"] = request.session["nextcloud"]
    os.environ["ONLYOFFICE"] = request.session["onlyoffice"]
    os.environ["COLLABORA"] = request.session["collabora"]
    os.environ["MATRIX"] = request.session["matrix"]
    os.environ["JITSI"] = request.session["jitsi"]
    os.environ["XFCE"] = request.session["xfce"]

    # Create env.sh file
    try:
        with open("/usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh", "w") as f:
            f.write(f"export DOMAIN={os.environ['DOMAIN']}\n")
            f.write(f"export IP={os.environ['IP']}\n")
            f.write(f"export ADMIN_PASSWORD={os.environ['ADMIN_PASSWORD']}\n")
            f.write(f"export LDAP_DC={os.environ['LDAP_DC']}\n")
    except Exception as e:
        message = f"Error while creating env.sh file: {str(e)} (If you are in a development environment, this is okay. If you are in a production environment, please check your installation.)"

    # Run installation script
    # if file /usr/share/linux-arbeitsplatz/unix/unix_scripts/general/installation_running exists
    if not os.path.isfile("/usr/share/linux-arbeitsplatz/unix/unix_scripts/general/installation_running"):
        if os.path.isfile("/usr/share/linux-arbeitsplatz/unix/unix_scripts/general/install.sh"):
            subprocess.Popen(["/usr/bin/bash", "/usr/share/linux-arbeitsplatz/unix/unix_scripts/general/install.sh"], cwd="/usr/share/linux-arbeitsplatz/unix/unix_scripts/general/" )
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


def etc_hosts(request):
    env = unix.get_env_sh_variables()
    etc_hosts = f"{env['IP']} {env['DOMAIN']}"
    for subdomain in subdomains:
        etc_hosts += f" {subdomain}.{env['DOMAIN']}"
    # Also get all subdomains from installed addons
    addons = unix.get_all_addon_modules()
    for addon in addons:
        if "url" in addon:
            etc_hosts += f" {addon['url']}.{env['DOMAIN']}"
    return HttpResponse(etc_hosts)
    # Generate /etc/hosts file of IP and the subdomains with the domain
