from django.shortcuts import render
import unix.forms as forms
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.models import User
from idm.idm import get_admin_user
import unix.unix_scripts.cfg as cfg
from unix.unix_scripts.general.update_email_settings import update_email_settings
from .forms import EmailConfiguration, AddonForm
from django.urls import reverse
import time
import unix.unix_scripts.unix as unix
import unix.email as email
import idm.ldap
from lac.templates import process_overview_dict, message
import idm.forms
import json

# Create your views here.
@staff_member_required(login_url=settings.LOGIN_URL)
# System Management
def unix_index(request):
    backup_information = unix.get_borg_information_for_dashboard()
    disks_stats = unix.get_disks_stats()
    system_information = unix.get_system_information()
    update_information = unix.get_update_information()
    
    return render(request, "unix/system_management.html", {"backup_information": backup_information, "disks_stats": disks_stats, "system_information": system_information, "update_information": update_information})


@staff_member_required(login_url=settings.LOGIN_URL)
def set_update_configuration(request):
    if request.method == "POST":
        software_modules = unix.get_software_modules()
        for module in software_modules:
            key = module["id"]
            configKey = key.upper().replace("-", "_") + "_AUTOMATIC_UPDATES"
            if request.POST.get(key, "") == "on":
                unix.set_value(configKey, "True")
            else:
                unix.set_value(configKey, "False")
        if request.POST.get("system", "") == "on":
            unix.set_value("SYSTEM_AUTOMATIC_UPDATES", "True")
        else:
            unix.set_value("SYSTEM_AUTOMATIC_UPDATES", "False")
        if request.POST.get("libre_workspace", "") == "on":
            unix.set_value("LIBRE_WORKSPACE_AUTOMATIC_UPDATES", "True")
        else:
            unix.set_value("LIBRE_WORKSPACE_AUTOMATIC_UPDATES", "False")
        unix.set_value("UPDATE_TIME", request.POST.get("time", "02:00"))
    return redirect("unix_index")

@staff_member_required(login_url=settings.LOGIN_URL)
def backup_settings(request):
    message = ""
    current_config = {
        "enabled": unix.is_backup_enabled(),
        "borg_repository": unix.get_value("BORG_REPOSITORY"),
        "borg_encryption": unix.get_value("BORG_ENCRYPTION") == "true",
        "borg_passphrase": unix.get_value("BORG_PASSPHRASE"),
        "daily_backup_time": unix.get_value("BORG_BACKUP_TIME"),
        "keep_daily_backups": unix.get_value("BORG_KEEP_DAILY"),
        "keep_weekly_backups": unix.get_value("BORG_KEEP_WEEKLY"),
        "keep_monthly_backups": unix.get_value("BORG_KEEP_MONTHLY"),
        "borg_repo_is_on_synology": unix.get_value("REMOTEPATH") != "",
        "trusted_fingerprint": unix.get_trusted_fingerprint()
    }
    form = forms.BackupSettings(initial=current_config)
    if request.method == "POST":
        form = forms.BackupSettings(request.POST)
        if form.is_valid():
            unix.set_backup_enabled(form.cleaned_data["enabled"])
            unix.set_value("BORG_REPOSITORY", form.cleaned_data["borg_repository"])
            unix.set_value("BORG_ENCRYPTION", "true" if form.cleaned_data["borg_encryption"] else "false")
            unix.set_value("BORG_PASSPHRASE", form.cleaned_data["borg_passphrase"].replace("$", "\$"))
            unix.set_value("BORG_BACKUP_TIME", form.cleaned_data["daily_backup_time"])
            unix.set_value("BORG_KEEP_DAILY", form.cleaned_data["keep_daily_backups"])
            unix.set_value("BORG_KEEP_WEEKLY", form.cleaned_data["keep_weekly_backups"])
            unix.set_value("BORG_KEEP_MONTHLY", form.cleaned_data["keep_monthly_backups"])
            unix.set_value("REMOTEPATH", "/usr/local/bin/borg" if form.cleaned_data["borg_repo_is_on_synology"] else "")
            unix.set_trusted_fingerprint(form.cleaned_data["trusted_fingerprint"])
            # message = "Einstellungen gespeichert."
            message = "Einstellungen gespeichert."
        else:
            message = "Einstellungen konnten nicht gespeichert werden."
    public_key = unix.get_public_key()
    return render(request, "unix/backup_settings.html", {"form": form, "message": message, "public_key": public_key})


@staff_member_required(login_url=settings.LOGIN_URL)
def retry_backup(request):
    unix.retry_backup()
    time.sleep(1)
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def update_system(request):
    unix.update_system()
    time.sleep(1)
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def reboot_system(request):
    unix.reboot_system()
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def shutdown_system(request):
    unix.shutdown_system()
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def start_all_services(request):
    unix.start_all_services()
    time.sleep(1)
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def stop_all_services(request):
    unix.stop_all_services()
    time.sleep(1)
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def data_management(request):
    partitions = unix.get_partitions()
    data_export_status = unix.get_data_export_status()
    rsync_history = unix.get_rsync_history()
    if unix.is_nextcloud_available():
        nextcloud_user_directories = unix.get_nextcloud_user_directories()
        nextcloud_import_process_running = unix.nextcloud_import_process_running()
    else:
        nextcloud_user_directories = []
        nextcloud_import_process_running = False
    return render(request, "unix/data_management.html", {"partitions": partitions, "data_export_status": data_export_status, "rsync_history": rsync_history, "nextcloud_user_directories": nextcloud_user_directories, "nextcloud_import_process_running": nextcloud_import_process_running})


@staff_member_required(login_url=settings.LOGIN_URL)
def mount(request, partition):
    message = unix.mount(partition)
    if message != "":
        return HttpResponse("Fehler beim Einhängen: " + message)
    time.sleep(1)
    return redirect("data_management")


@staff_member_required(login_url=settings.LOGIN_URL)
def umount(request, partition):
    message = unix.umount(partition)
    if message != "":
        return HttpResponse("Fehler beim Aushängen: " + message)
    time.sleep(1)
    return redirect("data_management")


@staff_member_required(login_url=settings.LOGIN_URL)
def data_export(request):
    if request.method == "POST":
        partition = request.POST.get("partition-export", "")
    else:
        return HttpResponse("Fehler: POST Request erwartet")
    if partition == "":
        return HttpResponse("Fehler: Keine Partition ausgewählt")
    partition += "/libre_workspace_export/"
    unix.export_data(partition)
    time.sleep(1)
    return redirect("data_management")


@staff_member_required(login_url=settings.LOGIN_URL)
def abort_current_data_export(request):
    unix.abort_current_data_export()
    time.sleep(1)
    return redirect("data_management")


@staff_member_required(login_url=settings.LOGIN_URL)
def data_import_1(request):
    if request.method == "POST":
        current_directory = request.POST.get("current_directory", "")
        if current_directory == "":
            return HttpResponse("Fehler: Kein Verzeichnis angegeben")
        # The user is the nextcloud path to the user directory
        user_import = request.POST.get("user_import", "")
        if user_import == "":
            return HttpResponse("Fehler: Kein Benutzer angegeben")
        request.session["current_directory"] = current_directory
        request.session["user_import"] = user_import
        request.session["redirection_after_selection"] = "data_import_2"
        request.session["redirection_on_cancel"] = "data_management"
        request.session["description"] = "Bitte wählen Sie das Verzeichnis aus, welches Sie importieren möchten."
        
        return redirect("pick_folder")
    
@staff_member_required(login_url=settings.LOGIN_URL)
def data_import_2(request):
    if request.session["current_directory"] == "/":
        return HttpResponse("Fehler: Das Root-Verzeichnis kann nicht importiert werden")
    unix.import_folder_to_nextcloud_user(request.session["current_directory"], request.session["user_import"])
    time.sleep(1)
    return redirect("data_management")
    

# Session: current_directory*, redirection_after_selection, redirection_on_cancel, description
# Also if a file is selected it will be stored in the session variable "current_directory"
# If allow_files is set to "True" the user can select a file
@staff_member_required(login_url=settings.LOGIN_URL)
def pick_path(request):
    allow_files = False
    if request.session.get("allow_files", "") == "True":
        allow_files = True
    if request.session.get("current_directory", "") == "":
        return HttpResponse("Fehler: Kein Verzeichnis angegeben")
    description = request.session.get("description", "")


    if request.method == "POST":
        if request.POST.get("cancel", "") != "":
            return redirect(request.session["redirection_on_cancel"])
        if request.POST.get("pick", "") != "":
            if request.POST.get("pick", "") == "..":
                request.session["current_directory"] = unix.get_directory_above(request.session["current_directory"])
            else:
                # Check if the selected path is a file
                if unix.is_path_a_file(request.session["current_directory"] + "/" + request.POST.get("pick", "")):
                    if allow_files:
                        request.session["current_directory"] = request.session["current_directory"] + "/" + request.POST.get("pick", "")
                        request.session["allow_files"] = request.POST.get("allow_files", "False")
                        return redirect(request.session["redirection_after_selection"])
                    else:
                        request.session["allow_files"] = request.POST.get("allow_files", "False")
                        return HttpResponse("Fehler: Es wurde eine Datei ausgewählt, aber ein Verzeichnis erwartet.")                    
                request.session["current_directory"] = request.session["current_directory"] + "/" + request.POST.get("pick", "")
            request.session["current_directory"] = request.session["current_directory"].replace("//", "/")
        if request.POST.get("select", "") != "":
            request.session["allow_files"] = request.POST.get("allow_files", "False")
            return redirect(request.session["redirection_after_selection"])

    folder_list = unix.get_folder_list(request.session["current_directory"])
    file_list = unix.get_file_list(request.session["current_directory"])
    return render(request, "unix/pick_folder.html", {"description": description, "folder_list": folder_list, "current_directory": request.session["current_directory"], "file_list": file_list, "enable_file_link": allow_files})


# This is only for system messages to the admin user
# We are using the djano module here
# This is only for local scripts.
# We are checking if the remote ip address is 127.0.0.1
def unix_send_mail(request):
    if request.method != "POST":
        return HttpResponse("Unauthorized")

    # if ip address 127.0.0.1 return
    if request.META.get("REMOTE_ADDR", "") != "127.0.0.1":
        return HttpResponse("Unauthorized")
    
    # Get admin email address
    admin_user = get_admin_user()
  
    recipient = request.POST.get("recipient", "")
    if recipient == "":
        if admin_user.get("mail", None) != None:
            recipient = admin_user["mail"]
        if recipient == "":
            return HttpResponseBadRequest("No recipient given and no admin email address found")
    subject = request.POST.get("subject", "")
    subject += f" - ({unix.get_libre_workspace_name()})"
    message = request.POST.get("message", "").replace("\\n", "\n")
    message += f"\n\nMessage from: {unix.get_libre_workspace_name()}"
    attachment_path = request.POST.get("attachment_path", "")

    email.send_mail(recipient, subject, message, attachment_path)

    return HttpResponse("Mail send successfully")


@staff_member_required(login_url=settings.LOGIN_URL)
def file_explorer(request):
    current_directory = request.session.get("current_directory", "/")

    if request.method == "POST":
        pick = request.POST.get("pick", "")
        if pick == "..":
            current_directory = unix.get_directory_above(current_directory)
        else:
            current_directory = current_directory + "/" + pick
    
    current_directory = current_directory.replace("//", "/")
    folder_list = unix.get_folder_list(current_directory)
    file_list = unix.get_file_list(current_directory)
    request.session["current_directory"] = current_directory
   
    return render(request, "unix/file_explorer.html", {"folder_list": folder_list, "current_directory": current_directory, "file_list": file_list})


@staff_member_required(login_url=settings.LOGIN_URL)
# Thats the config dashboard in system configuration
def email_configuration(request):
    message = ""
    current_email_conf = {
        "server": cfg.get_value("EMAIL_HOST", ""),
        "port": cfg.get_value("EMAIL_PORT", ""),
        "user": cfg.get_value("EMAIL_HOST_USER", ""),
        "email": cfg.get_value("EMAIL_HOST_EMAIL", ""),
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
            cfg.set_value("EMAIL_HOST", form.cleaned_data["server"])
            cfg.set_value("EMAIL_PORT", form.cleaned_data["port"])
            cfg.set_value("EMAIL_HOST_USER", form.cleaned_data["user"])
            cfg.set_value("EMAIL_HOST_EMAIL", form.cleaned_data["email"])
            if form.cleaned_data["password"] != "":
                # We need to escape the $ sign because of the bash syntax in our config file
                cfg.set_value("EMAIL_HOST_PASSWORD", form.cleaned_data["password"].replace("$", "\$"))
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
            update_email_settings(form.cleaned_data)
            unix.restart_linux_arbeitsplatz_web()

    return render(request, "unix/email_configuration.html", {"current_email_conf": current_email_conf, "form": form, "message": message})


@staff_member_required(login_url=settings.LOGIN_URL)
def system_configuration(request):
    return render(request, "unix/system_configuration.html")


@staff_member_required(login_url=settings.LOGIN_URL)
def module_management(request):
    message = ""
    if request.method == "POST":
        form = forms.OnlineOfficeInstallationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data["online_office"] == "Deaktivieren" and (unix.is_onlyoffice_available() or unix.is_collabora_available()):
                unix.remove_module("onlyoffice")
                unix.remove_module("collabora")
            elif data["online_office"] == "OnlyOffice" and (not unix.is_onlyoffice_available() or unix.is_collabora_available()):
                unix.remove_module("collabora")
                unix.setup_module("onlyoffice")
            elif data["online_office"] == "Collabora" and (unix.is_onlyoffice_available() or not unix.is_collabora_available()):
                unix.remove_module("onlyoffice")
                unix.setup_module("collabora")
            message = "Änderungen werden angewendet. Dies kann einige Minuten dauern."
        
    modules = unix.get_software_modules()
    # Remove the modules with the id "onlyoffice" and "collabora"
    modules = [module for module in modules if module["id"] not in ["onlyoffice", "collabora"]]
    # We check here if the message is empty because when an action is running the form selection (the pre selected) will be wrong
    if unix.is_nextcloud_available() and message == "":
        form = forms.OnlineOfficeInstallationForm()
        currentOnlineModule = unix.get_online_office_module()
        match currentOnlineModule:
            case "onlyoffice":
                form.fields["online_office"].initial = "OnlyOffice"
            case "collabora":
                form.fields["online_office"].initial = "Collabora"
            case _:
                form.fields["online_office"].initial = "Deaktivieren"
    else:
        form = ""
    return render(request, "unix/module_management.html" , {"modules": modules, "form": form, "message": message})


@staff_member_required(login_url=settings.LOGIN_URL)
def install_module(request, name):
    response = unix.setup_module(name)
    if response != None:
        return render(request, "lac/message.html", {"message": f"{name} konnte nicht deinstalliert werden: {response}", "url": reverse("dashboard")})
    return render(request, "lac/message.html", {"message": f"{name} wird installiert. Dies kann einige Minuten dauern.", "url": reverse("dashboard")})


@staff_member_required(login_url=settings.LOGIN_URL)
def uninstall_module(request, name):
    response = unix.remove_module(name)
    if response != None:
        return render(request, "lac/message.html", {"message": f"{name} konnte nicht deinstalliert werden: {response}", "url": reverse("dashboard")})
    return render(request, "lac/message.html", {"message": f"{name} wird deinstalliert. Dies kann einige Minuten dauern.", "url": reverse("dashboard")})


@staff_member_required(login_url=settings.LOGIN_URL)
def mount_backups(request):
    message = unix.mount_backups()
    if message != None:
        return render(request, "lac/message.html", {"message": f"Fehler beim Einhängen: {message}", "url": reverse("unix_index")})
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def umount_backups(request):
    message = unix.umount_backups()
    if message != None:
        return render(request, "lac/message.html", {"message": f"Fehler beim Aushängen: {message}", "url": reverse("unix_index")})
    return redirect("unix_index")


# We are getting all information from request.session
@staff_member_required(login_url=settings.LOGIN_URL)
def recover_path(request):
    error_page = render(request, "lac/message.html", {"message": "Fehler: Das Verzeichnis kann nicht wiederhergestellt werden. Bitte wählen Sie ein Verzeichnis in <code>/backups</code> aus.", "url": reverse("unix_index")})

    # Check if everything is okay
    path = request.session["current_directory"]
    if not path.startswith("/backups"):
        return error_page
    # Ensure that the path is not ending with /
    if path.endswith("/"):
        path = path[:-1]
    # Get the number of / in the path
    path_parts = path.split("/")
    if len(path_parts) <= 3:
        return error_page
    
    # Check confirmation
    if request.method == "POST":
        # Do the recovery
        if request.POST.get("confirm", "") != "on":
            return render(request, "lac/message.html", {"message": "Sie müssen die Wiederherstellung bestätigen.", "url": reverse("recover_path")})
        
        response = unix.recover_file_or_dir(path)
        if response != None:
            return render(request, "lac/message.html", {"message": f"Das Verzeichnis konnte nicht wiederhergestellt werden: <code>{response}</code>", "url": reverse("unix_index")})
        return render(request, "lac/message.html", {"message": "Wiederherstellung wird durchgeführt. Dies kann einige Minuten dauern.", "url": reverse("unix_index")})
    else:
        # Render the confirmation page
        return render(request, "lac/confirm.html", {"message": f"Bitte bestätigen Sie die Wiederherstellung von {path}.<br>Die Wiederherstellung wird bestehende Dateien überschreiben.", "url_cancel": reverse("unix_index")})


@staff_member_required(login_url=settings.LOGIN_URL)
def enter_recovery_selector(request):
    request.session["redirection_after_selection"] = "recover_path"
    request.session["redirection_on_cancel"] = "data_management"
    request.session["description"] = "Bitte wählen Sie das Verzeichnis oder die Datei aus, welche Sie wiederherstellen möchten. Die Wiederherstellung wird bestehende Dateien überschreiben."
    request.session["allow_files"] = "True"
    request.session["current_directory"] = "/backups"
    return redirect("pick_folder")


@staff_member_required(login_url=settings.LOGIN_URL)
def test_mail(request):
    user_information = idm.ldap.get_user_information_of_cn(request.user.username)
    mail_adress = user_information.get("mail", "")
    if mail_adress == "" or mail_adress == None:
        return render(request, "lac/message.html", {"message": "Keine E-Mail-Adresse gefunden. Bitte definieren Sie eine Mail-Adresse in Ihren Benutzereinstellungen.", "url": reverse("user_settings")})
    message = email.send_mail(mail_adress, "Testmail - Libre Workspace", "Das ist eine Testmail.\nIhre Mail-Einstellungen scheinen korrekt zu sein.")
    if message != None:
        return render(request, "lac/message.html", {"message": f"Testmail konnte nicht versendet werden: <code>{message}</code>", "url": reverse("email_configuration")})
    return render(request, "lac/message.html", {"message": "Testmail wurde erfolgreich versendet. Bitte überprüfen Sie Ihr Postfach.", "url": reverse("email_configuration")})


@staff_member_required(login_url=settings.LOGIN_URL)
def addons(request):
    overview = process_overview_dict({
        "heading": "Addon Verwaltung",
        "element_name": "Addon",
        "element_url_key": "id",
        "elements": unix.get_all_addon_modules(),
        "t_headings": ["Name", "Beschreibung", "Author"],
        "t_keys": ["name", "description", "author"],
        "add_url_name": "add_addon",
        "delete_url_name": "remove_addon",
    })
    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def add_addon(request):
    if request.method == "POST":
        file = request.FILES["file"]
        # Move the file to /tmp folder
        # Check if the file is a zip file
        if not file.name.endswith(".zip"):
            return message(request, "Die Datei muss eine Zip-Datei sein.", "add_addon")
        # Move the file to /tmp
        with open("/tmp/" + file.name, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        # Install the addon
        response = unix.install_addon("/tmp/" + file.name)
        if response != None:
            return message(request, f"Das Addon konnte nicht installiert werden: {response}", "addons")
        return message(request, "Das Addon wurde installiert.", "addons")
    form = AddonForm()
    return render(request, "lac/create_x.html", {"form": form, "heading": "Add-On hinzufügen", "hide_buttons_top": "True"})

@staff_member_required(login_url=settings.LOGIN_URL)
def remove_addon(request, addon_id):
    if unix.is_module_installed(addon_id):
        return message(request, f"Das Addon kann nicht deinstalliert werden, da es noch in Benutzung ist.", "addons")
    response = unix.uninstall_addon(addon_id)
    if response != None:
        return message(request, f"Das Addon konnte nicht deinstalliert werden: <code>{response}</code>", "addons")
    return message(request, f"Das Addon wurde deinstalliert.", "addons")


@staff_member_required(login_url=settings.LOGIN_URL)
def change_libre_workspace_name(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        unix.set_value("LIBRE_WORKSPACE_NAME", name)
        return message(request, "Der Name wurde geändert.", "unix_index")
    form = forms.ChangeLibreWorkspaceNameForm()
    return render(request, "lac/create_x.html", {"form": form, "heading": "Libre Workspace Name ändern", "hide_buttons_top": "True", "url": reverse("unix_index")})


@staff_member_required(login_url=settings.LOGIN_URL)
def critical_system_configuration(request):
    return render(request, "unix/critical_system_configuration.html")


@staff_member_required(login_url=settings.LOGIN_URL)
def change_ip_address(request):
    if request.method == "POST":
        ip = request.POST.get("ip", "")
        # Check if the ip is valid
        if not unix.is_valid_ip(ip):
            return message(request, "Die IP-Adresse ist nicht gültig.", "critical_system_configuration")
        unix.set_value("IP", ip)
        return message(request, "Die IP-Adresse wurde geändert.", "critical_system_configuration")
    form = forms.ChangeIpAdressForm()
    return render(request, "lac/generic_form.html", 
                  {"form": form, 
                   "heading": "IP-Adresse ändern",
                   "action": "Ändern",
                   "hide_buttons_top": "True", 
                   "url": reverse("critical_system_configuration"), 
                   "danger": "True",
                   "description": "Bitte geben Sie die neue IP-Adresse des Servers ein. Der Server wird direkt danach neu gestartet."})


@staff_member_required(login_url=settings.LOGIN_URL)
def change_master_password(request):
    if request.method == "POST":
        current_password = unix.get_administrator_password()
        if request.POST.get("old_password", "") != current_password:
            return message(request, "Das aktuelle Passwort ist falsch.", "critical_system_configuration")
        if request.POST.get("new_password", "") != request.POST.get("new_password_repeat", ""):
            return message(request, "Die neuen Passwörter stimmen nicht überein.", "critical_system_configuration")
        password = request.POST.get("new_password", "")
        errors = unix.password_challenge(password)
        if errors == "":
            unix.change_master_password(password)
            return message(request, "Das Master-Passwort wurde geändert.", "critical_system_configuration")
        else:
            return message(request, f"Das neue Passwort ist nicht sicher genug: {errors}", "critical_system_configuration")
    form = idm.forms.PasswordForm()
    return render(request, "lac/generic_form.html", 
                  {"form": form, 
                   "heading": "Master-Passwort ändern",
                   "action": "Ändern",
                   "hide_buttons_top": "True", 
                   "url": reverse("critical_system_configuration"), 
                   "danger": "True",
                   "description": "Bitte geben Sie das neue Master-Passwort ein. Das Master-Passwort wird direkt danach geändert und der Server wird direkt neu gestartet."})


@staff_member_required(login_url=settings.LOGIN_URL)
def miscellaneous_settings(request):
    form = forms.MiscellaneousSettingsForm()
    if request.method == "POST":
        form = forms.MiscellaneousSettingsForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["disable_nextcloud_user_administration"]:
                unix.disable_nextcloud_user_administration()
            else:
                unix.enable_nextcloud_user_administration()
            return message(request, "Einstellungen gespeichert.", "system_configuration")
    form.fields["disable_nextcloud_user_administration"].initial = not unix.is_nextcloud_user_administration_enabled()
    return render(request, "lac/generic_form.html", {"form": form, "heading": "Verschiedene Einstellungen", "action": "Speichern", "url": reverse("system_configuration"), "hide_buttons_top": "True"})


# API-Call
@staff_member_required(login_url=settings.LOGIN_URL)
def system_information(request):
    data = json.dumps(unix.get_system_information())
    return HttpResponse(data, content_type="application/json")


@staff_member_required(login_url=settings.LOGIN_URL)
def additional_services(request):
    if request.method == "POST":
        form = forms.AdditionalServicesForm(request.POST)
        if form.is_valid():
            unix.set_additional_services_control_files(form.cleaned_data["start_additional_services"], form.cleaned_data["stop_additional_services"])
            return message(request, "Änderungen gespeichert.", "system_configuration")
        return message(request, "Fehler: Eingaben ungültig.", "additional_services")
    
    form = forms.AdditionalServicesForm()
    (start_additional_services, stop_additional_services) = unix.get_additional_services_control_files()
    form.fields["start_additional_services"].initial = start_additional_services
    form.fields["stop_additional_services"].initial = stop_additional_services
    return render(request, "lac/generic_form.html", {"form": form, "heading": "Zusätzliche Dienste", "action": "Speichern", "url": reverse("system_configuration"), "hide_buttons_top": "True", "description": "Fügen Sie gültige Bash-Befehle hinzu, welche für das Starten und Stoppen ihrer zusätlichen Dienste ausgeführt werden sollen. Verwenden Sie keine cd-Befehle oder ähnliches."})


@staff_member_required(login_url=settings.LOGIN_URL)
def update_libre_workspace(request):
    m = unix.update_libre_workspace()
    if message != None:
        return message(request, f"Libre Workspace konnte nicht aktualisiert werden: <code>{m}</code>", "unix_index")
    return message(request, "Libre Workspace wird aktualisiert. Dies kann einige Minuten dauern. Libre Workspace ist für kurze Zeit nicht erreichbar.", "unix_index")