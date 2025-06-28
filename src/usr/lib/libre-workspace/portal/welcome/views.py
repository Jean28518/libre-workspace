from django.shortcuts import render, redirect
import os
import subprocess
from django.conf import settings
import unix.unix_scripts.unix as unix
from django.http import HttpResponse
from lac.templates import message as message_func
from django.utils.translation import gettext as _


# List of subdomains
subdomains = ["cloud", "office", "portal", "la", "chat", "meet", "element", "matrix", "desktop"]

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
            message = _("Passwords do not match. Please try again.")
        if message == "":
            return redirect("welcome_select_apps")
        
    ip = os.popen("hostname -I").read().split(" ")[0]
    if ":" in ip:
        ip = f"[{ip}]" # IPv6

    return render(request, "welcome/welcome_start.html", {"message": message, "hide_login_button": True, "ip": ip})


def welcome_select_apps(request):
    if request.method == "POST":
        request.session["nextcloud"] = request.POST.get("nextcloud", "")
        if request.POST.get("online_office", "") == "onlyoffice" and request.POST.get("nextcloud", ""):
            request.session["onlyoffice"] = "onlyoffice"
        elif request.POST.get("online_office", "") == "collabora" and request.POST.get("nextcloud", ""):
            request.session["collabora"] = "collabora"
        request.session["desktop"] = request.POST.get("desktop", "")
        request.session["matrix"] = request.POST.get("matrix", "")
        request.session["jitsi"] = request.POST.get("jitsi", "")
        request.session["xfce"] = request.POST.get("xfce", "")

        if not (request.session["nextcloud"] or request.session["matrix"] or request.session["jitsi"] or request.session["xfce"] or request.session["desktop"]):
            return redirect("libreworkspace_lite")

        return redirect("welcome_dns_settings")

    return render(request, "welcome/welcome_select_apps.html", {"hide_login_button": True})


def welcome_dns_settings(request):
    message = ""
    if request.method == "POST":
        request.session["visibility"] = request.POST.get("visibility", "")
        if request.session["visibility"] == "public" and request.POST.get("domain", "") == "":
            message = _("Please provide a domain.")
        if request.session["visibility"] == "public" and message == "":
            request.session["domain"] = request.POST.get("domain", "")
            message = check_domain(request.session["domain"], True)
            request.session["domain"] = request.session["domain"].lower()
            request.session["shortend_domain"] = get_shortend_domain(request.session["domain"])
            request.session["ldap_dc"] = get_ldap_dc(request.session["domain"])
        else:
            request.session["domain"] = "int.de"
            request.session["shortend_domain"] = "int.de"
            request.session["ldap_dc"] = "dc=int,dc=de"
        if message == "" or message == None:
            return redirect("installation_running")
    return render(request, "welcome/welcome_dns_settings.html", {"message": message, "subdomains": subdomains, "hide_login_button": True})


def libreworkspace_lite(request):
    message = ""
    if request.method == "POST":
        if request.POST["visibility"] == "port":
            request.session["custom_access"] = ":23816"
        else:
            request.session["custom_access"] = request.POST.get("portal_domain_field", "")
            message = check_domain(request.session["custom_access"], True)
        if message == "" or message == None:
            message = check_domain(request.POST.get("further_root_domain", "int.de"), True)
            if message == "" or message == None:
                request.session["domain"] = request.POST.get("further_root_domain", "int.de")
                request.session["ldap_dc"] = get_ldap_dc(request.session["domain"])
                request.session["shortend_domain"] = get_shortend_domain(request.session["domain"])
                return redirect("installation_running")
    return render(request, "welcome/libreworkspace_lite.html", {"message": message, "hide_login_button": True})


def check_domain(domain, subdomain=False):
    if domain == "":
        return _("Please provide a domain.")
    if domain.count(".") != 1 and not subdomain:
        return _("Please ensure you only provide the domain and no subdomain.")
    if not (domain.count(".") >= 1 and len(domain.split(".")[-2]) > 0 and len(domain.split(".")[-1])):
        return _("Please provide a valid domain.")
    lvl1 = domain.split(".")[-1]
    if len(lvl1) > 12:
        return _("Please ensure the top-level domain (TLD) is not longer than 12 characters.")
    return None


def get_ldap_dc(domain):
    lvl1 = domain.split(".")[-1]
    if len(lvl1) > 12:
        return _("Please ensure the top-level domain (TLD) is not longer than 12 characters.")
    other_parts = domain.replace(lvl1, "")
    # remove the last dot
    other_parts = other_parts[:-1]
    # We have to shorten because of the NET BIOS name limitations.
    shortend_other_parts = other_parts[:12-len(lvl1)-1]
    return "dc=" + shortend_other_parts.replace(".", ",dc=") + ",dc=" + lvl1


def get_shortend_domain(domain):
    print("HELLO WORLD!")
    lvl1 = domain.split(".")[-1]
    other_parts = domain.replace(lvl1, "")
    # remove the last dot
    other_parts = other_parts[:-1]
    # We have to shorten because of the NET BIOS name limitations.
    shortend_other_parts = other_parts[:12-len(lvl1)-1]
    print(shortend_other_parts + "." + lvl1)
    return shortend_other_parts + "." + lvl1


def installation_running(request):
    if os.environ["LINUX_ARBEITSPLATZ_CONFIGURED"] == "True":
        return message_func(request, _("Libre Workspace is already configured. Please log in."))
    message = ""
    os.environ["DOMAIN"] = request.session["domain"]
    os.environ["SHORTEND_DOMAIN"] = request.session["shortend_domain"]
    os.environ["ADMIN_PASSWORD"] = request.session["password"]
    # Get output of script: in lac/unix/unix_scripts/get_ip.sh
    os.environ["IP"] = os.popen("hostname -I").read().split(" ")[0]
    os.environ["LDAP_DC"] = request.session["ldap_dc"]
    # Run basics script
    os.environ["SAMBA_DC"] = request.session["nextcloud"] or request.session["matrix"] or request.session["jitsi"] or request.session["desktop"]
    os.environ["NEXTCLOUD"] = request.session["nextcloud"]
    os.environ["ONLYOFFICE"] = request.session.get("onlyoffice", "")
    os.environ["COLLABORA"] = request.session.get("collabora", "")
    os.environ["DESKTOP"] = request.session["desktop"]
    os.environ["MATRIX"] = request.session["matrix"]
    os.environ["JITSI"] = request.session["jitsi"]
    os.environ["XFCE"] = request.session["xfce"]
    os.environ["CUSTOM_ACCESS"] = request.session.get("custom_access", "")

    print("DOMAIN: ", os.environ["DOMAIN"])
    print("IP: ", os.environ["IP"])
    print("LDAP_DC: ", os.environ["LDAP_DC"])
    print("SHORTEND_DOMAIN: ", os.environ["SHORTEND_DOMAIN"])

    # Create /etc/libre-workspace/libre-workspace.env file
    try:
        with open("/etc/libre-workspace/libre-workspace.env", "w") as f:
            f.write(f"export DOMAIN={os.environ['DOMAIN']}\n")
            f.write(f"export IP={os.environ['IP']}\n")
            f.write(f"export ADMIN_PASSWORD={os.environ['ADMIN_PASSWORD']}\n")
            f.write(f"export LDAP_DC={os.environ['LDAP_DC']}\n")
    except Exception as e:
        message = _("Error while creating /etc/libre-workspace/libre-workspace.env file: %(error_message)s (If you are in a development environment, this is okay. If you are in a production environment, please check your installation.)") % {"error_message": str(e)}

    # Run installation script
    # if file /var/lib/libre-workspace/portal/installation_running exists
    if not os.path.isfile("/var/lib/libre-workspace/portal/installation_running"):
        if os.path.isfile("/usr/lib/libre-workspace/portal/unix/unix_scripts/general/install.sh"):
            subprocess.Popen(["/usr/bin/bash", "/usr/lib/libre-workspace/portal/unix/unix_scripts/general/install.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/general/" )
        else:
            print(_("WARNING: Installation script not found! If you are in a development environment, that's okay. If you are in a production environment, please check your installation."))
            message = _("WARNING: Installation script not found! If you are in a development environment, that's okay. If you are in a production environment, please check your installation.")
    
    if not "cert" in subdomains:
        subdomains.append("cert")

    custom_access = os.environ.get("CUSTOM_ACCESS", "")
    if custom_access == ":23816":
        custom_access = os.environ["IP"] + custom_access

    variables = {
        "message": message, 
        "subdomains": subdomains, 
        "domain": os.environ["DOMAIN"],
        "ip": os.environ["IP"],
        "hide_login_button": True,
        "custom_access": custom_access
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