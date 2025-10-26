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
from .forms import EmailConfiguration, AddonForm, IgnoredDomainsForm
from django.urls import reverse
import time
import unix.unix_scripts.unix as unix
import unix.email as email
import idm.ldap
from lac.templates import process_overview_dict, message
import idm.forms
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
import subprocess
import os

DISABLE_DANGEROUS_ADMIN_FUNCTIONS = os.environ.get("DISABLE_DANGEROUS_ADMIN_FUNCTIONS", "False") == "True"

# Create your views here.
@staff_member_required(login_url=settings.LOGIN_URL)
# System Management
def unix_index(request):
    backup_information = unix.get_borg_information_for_dashboard()
    disks_stats = unix.get_disks_stats()
    system_information = unix.get_system_information()
    update_information = unix.get_update_information()
    
    return render(request, "unix/system_management.html", {"backup_information": backup_information, "disks_stats": disks_stats, "system_information": system_information, "update_information": update_information, "backup_configuration_url": reverse("backup_settings")})


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
def backup_settings(request, additional_id=None):
    message = ""
    key_addition = ""
    if additional_id:
        key_addition = "_" + additional_id
    current_config = {
        "enabled": unix.is_backup_enabled(),
        "borg_repository": unix.get_value("BORG_REPOSITORY"+key_addition),
        "borg_encryption": unix.get_value("BORG_ENCRYPTION"+key_addition) == "true",
        "borg_passphrase": unix.get_value("BORG_PASSPHRASE"+key_addition),
        "daily_backup_time": unix.get_value("BORG_BACKUP_TIME"+key_addition),
        "keep_daily_backups": unix.get_value("BORG_KEEP_DAILY"+key_addition),
        "keep_weekly_backups": unix.get_value("BORG_KEEP_WEEKLY"+key_addition),
        "keep_monthly_backups": unix.get_value("BORG_KEEP_MONTHLY"+key_addition),
        "borg_repo_is_on_synology": unix.get_value("REMOTEPATH"+key_addition) != "",
        "trusted_fingerprint": unix.get_trusted_fingerprint(additional_id),
        "additional_borg_options": unix.get_value("ADDITIONAL_BORG_OPTIONS"+key_addition, "")
    }
    form = forms.BackupSettings(initial=current_config)
    if request.method == "POST":
        form = forms.BackupSettings(request.POST)
        if form.is_valid():
            unix.set_backup_enabled(form.cleaned_data["enabled"], additional_id)
            unix.set_value("BORG_REPOSITORY"+key_addition, form.cleaned_data["borg_repository"])
            unix.set_value("BORG_ENCRYPTION"+key_addition, "true" if form.cleaned_data["borg_encryption"] else "false")
            unix.set_value("BORG_PASSPHRASE"+key_addition, form.cleaned_data["borg_passphrase"].replace("$", "\$"))
            unix.set_value("BORG_BACKUP_TIME"+key_addition, form.cleaned_data["daily_backup_time"])
            unix.set_value("BORG_KEEP_DAILY"+key_addition, form.cleaned_data["keep_daily_backups"])
            unix.set_value("BORG_KEEP_WEEKLY"+key_addition, form.cleaned_data["keep_weekly_backups"])
            unix.set_value("BORG_KEEP_MONTHLY"+key_addition, form.cleaned_data["keep_monthly_backups"])
            unix.set_value("REMOTEPATH"+key_addition, "/usr/local/bin/borg" if form.cleaned_data["borg_repo_is_on_synology"] else "")
            unix.set_trusted_fingerprint(form.cleaned_data["trusted_fingerprint"], key_addition),
            unix.set_value("ADDITIONAL_BORG_OPTIONS"+key_addition, form.cleaned_data["additional_borg_options"])
            message = _("Settings saved.")
        else:
            message = _("Settings could not be saved.")
    public_key = unix.get_public_key()
    back_url = reverse("unix_index")
    if additional_id:
        back_url = reverse("additional_backup_configurations")

    backup_name = None
    if additional_id:
        backup_name = unix.get_value("ADDITIONAL_BACKUP_NAME_"+additional_id, "")
    return render(request, "unix/backup_settings.html", {"form": form, "message": message, "public_key": public_key, "back_url": back_url, "backup_name": backup_name})


@staff_member_required(login_url=settings.LOGIN_URL)
def backup_dashboard(request, additional_id):
    backup_information = unix.get_borg_information_for_dashboard(additional_id)
    backup_name = unix.get_value("ADDITIONAL_BACKUP_NAME_"+additional_id, "")
    backup_configuration_url = reverse("backup_settings", args=[additional_id])
    back_url = reverse("additional_backup_configurations")
    return render(request, "unix/backup_dashboard_standalone.html", {"backup_information": backup_information, "backup_name": backup_name, "backup_configuration_url": backup_configuration_url, "additional_id": additional_id, "back_url": back_url})

@staff_member_required(login_url=settings.LOGIN_URL)
def additional_backup_configurations(request):
    additional_backup_ids = unix.get_additional_backup_ids()
    overview = process_overview_dict({
        "heading": _("Additional Backup Configurations"),
        "element_name": _("Backup Configuration"),
        "element_url_key": "id",
        "elements": additional_backup_ids,
        "t_headings": [_("Name")],
        "t_keys": ["name"],
        "add_url_name": "add_additional_backup_configuration",
        "info_url_name": "backup_dashboard",
        "delete_url_name": "remove_additional_backup_configuration",
        "back_url_name": "unix_index",
    })
    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def add_additional_backup_configuration(request):
    form = forms.AdditionalBackupConfigurationForm()
    if request.method == "POST":
        form = forms.AdditionalBackupConfigurationForm(request.POST)
        if form.is_valid():
            id = unix.generate_random_id(10)
            unix.set_value("ADDITIONAL_BACKUP_NAME_"+id, form.cleaned_data["name"])
            subprocess.call(["mkdir", "-p", "/var/lib/libre-workspace/portal/additional_backup_"+id])
            return redirect("backup_settings", additional_id=id)
    return render(request, "lac/generic_form.html", {"form": form, "heading": _("Add Additional Backup Configuration"), "hide_buttons_top": "True", "action": _("Add"), "url": reverse("additional_backup_configurations")})


@staff_member_required(login_url=settings.LOGIN_URL)
def remove_additional_backup_configuration(request, additional_id):
    # Remove all the config keys with the additional id
    subprocess.call(["sed", "-i", f"/_{additional_id}/d", "/etc/libre-workspace/libre-workspace.conf"])

    subprocess.call(["rm", "-rf", "/var/lib/libre-workspace/portal/additional_backup_"+additional_id])
    return redirect("additional_backup_configurations")


@staff_member_required(login_url=settings.LOGIN_URL)
def retry_backup(request, additional_id=None):
    unix.retry_backup(additional_id)
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
    if unix.is_nextcloud_installed():
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
        return HttpResponse(_("Error mounting: %(message)s") % {"message": message})
    time.sleep(1)
    return redirect("data_management")


@staff_member_required(login_url=settings.LOGIN_URL)
def umount(request, partition):
    message = unix.umount(partition)
    if message != "":
        return HttpResponse(_("Error unmounting: %(message)s") % {"message": message})
    time.sleep(1)
    return redirect("data_management")


@staff_member_required(login_url=settings.LOGIN_URL)
def data_export(request):
    if request.method == "POST":
        partition = request.POST.get("partition-export", "")
    else:
        return HttpResponse(_("Error: POST Request expected"))
    if partition == "":
        return HttpResponse(_("Error: No partition selected"))
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
            return HttpResponse(_("Error: No directory specified"))
        # The user is the nextcloud path to the user directory
        user_import = request.POST.get("user_import", "")
        if user_import == "":
            return HttpResponse(_("Error: No user specified"))
        request.session["current_directory"] = current_directory
        request.session["user_import"] = user_import
        request.session["redirection_after_selection"] = "data_import_2"
        request.session["redirection_on_cancel"] = "data_management"
        request.session["description"] = _("Please select the directory you want to import.")
        
        return redirect("pick_folder")
    
@staff_member_required(login_url=settings.LOGIN_URL)
def data_import_2(request):
    if request.session["current_directory"] == "/":
        return HttpResponse(_("Error: The root directory cannot be imported"))
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
        return HttpResponse(_("Error: No directory specified"))
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
                        return HttpResponse(_("Error: A file was selected, but a directory was expected."))                    
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
# Disable csrf:
@csrf_exempt
def unix_send_mail(request):
    if request.method != "POST":
        return HttpResponseBadRequest(_("Only POST requests are allowed"))

    # if ip address 127.0.0.1 return unauthorized
    # (But because we are using caddy we are not using the ip address of the request)
    if request.META.get("REMOTE_ADDR", "") != "127.0.0.1":
        return HttpResponse(_("Unauthorized. Request not local."))
    
    # So we need to check additional headers
    # Check if the request is made not from caddy
    # Check if the request has the header X-Forwarded-For
    if request.META.get("HTTP_X_FORWARDED_FOR", "") != "":
        return HttpResponse(_("Unauthorized. Request is seems not directly made."))
    
    # Also we need the header for the lw admin token
    if request.POST.get("lw_admin_token", "") != unix.get_local_admin_token():
        return HttpResponse(_("Unauthorized. Token is not valid."))
    
    # Get admin email address
    admin_user = get_admin_user()
  
    recipient = request.POST.get("recipient", "")
    if recipient == "":
        if admin_user.get("mail", None) != None:
            recipient = admin_user["mail"]
        if recipient == "":
            return HttpResponseBadRequest(_("No recipient given and no admin email address found"))
        
    recipients = []
    recipients.append(recipient)
    for additional_recepient in unix.get_value("ADDITIONAL_MAIL_ADDRESSES_FOR_SYSTEM_MAILS", "").split(","):
        if additional_recepient != "":
            recipients.append(additional_recepient)
    
    subject = request.POST.get("subject", "")
    subject += f" - ({unix.get_libre_workspace_name()})"
    message = request.POST.get("message", "").replace("\\n", "\n")
    message += _("\n\nMessage from: %(libre_workspace_name)s") % {"libre_workspace_name": unix.get_libre_workspace_name()}
    attachment_path = request.POST.get("attachment_path", "")

    email.send_mail(recipients, subject, message, attachment_path)

    return HttpResponse(_("Mail sent successfully"))


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
            message = _("Email configuration saved.")
            mail_config = form.cleaned_data.copy()
            if (mail_config["password"] == ""):
                mail_config["password"] = current_email_conf["password"]
            update_email_settings(form.cleaned_data)
            unix.restart_libre_workspace_portal()

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
            if data["online_office"] == "Deaktivieren" and (unix.is_onlyoffice_installed() or unix.is_collabora_installed()):
                unix.remove_module("onlyoffice")
                unix.remove_module("collabora")
            elif data["online_office"] == "OnlyOffice" and (not unix.is_onlyoffice_installed() or unix.is_collabora_installed()):
                unix.remove_module("collabora")
                unix.setup_module("onlyoffice")
            elif data["online_office"] == "Collabora" and (unix.is_onlyoffice_installed() or not unix.is_collabora_installed()):
                unix.remove_module("onlyoffice")
                unix.setup_module("collabora")
            message = _("Changes are being applied. This may take a few minutes.")
        
    modules = unix.get_software_modules()
    # Remove the modules with the id "onlyoffice" and "collabora"
    modules = [module for module in modules if module["id"] not in ["onlyoffice", "collabora"]]
    # We check here if the message is empty because when an action is running the form selection (the pre selected) will be wrong
    if unix.is_nextcloud_installed() and message == "":
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
        return render(request, "lac/message.html", {"message": _("%(name)s could not be uninstalled: %(response)s") % {"name": name, "response": response}, "url": reverse("dashboard")})
    return render(request, "lac/message.html", {"message": _("%(name)s is being installed. This may take a few minutes.") % {"name": name}, "url": reverse("dashboard")})


@staff_member_required(login_url=settings.LOGIN_URL)
def uninstall_module(request, name):
    response = unix.remove_module(name)
    if response != None:
        return render(request, "lac/message.html", {"message": _("%(name)s could not be uninstalled: %(response)s") % {"name": name, "response": response}, "url": reverse("dashboard")})
    return render(request, "lac/message.html", {"message": _("%(name)s is being uninstalled. This may take a few minutes.") % {"name": name}, "url": reverse("dashboard")})


@staff_member_required(login_url=settings.LOGIN_URL)
def mount_backups(request, additional_id=None):
    message = unix.mount_backups(additional_id=additional_id)
    if message != None:
        return render(request, "lac/message.html", {"message": _("Error mounting: %(message)s") % {"message": message}, "url": reverse("unix_index")})
    if additional_id:
        return redirect("backup_dashboard", additional_id=additional_id)
    return redirect("unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def umount_backups(request, additional_id=None):
    message = unix.umount_backups(additional_id=additional_id)
    if message != None:
        return render(request, "lac/message.html", {"message": _("Error unmounting: %(message)s") % {"message": message}, "url": reverse("unix_index")})
    if additional_id:
        return redirect("backup_dashboard", additional_id=additional_id)
    return redirect("unix_index")


# We are getting all information from request.session
@staff_member_required(login_url=settings.LOGIN_URL)
def recover_path(request):
    error_page = render(request, "lac/message.html", {"message": _("Error: The directory cannot be restored. Please select a directory in <code>/backups</code>."), "url": reverse("unix_index")})

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
            return render(request, "lac/message.html", {"message": _("You must confirm the recovery."), "url": reverse("recover_path")})
        
        response = unix.recover_file_or_dir(path)
        if response != None:
            return render(request, "lac/message.html", {"message": _("The directory could not be restored: <code>%(response)s</code>") % {"response": response}, "url": reverse("unix_index")})
        return render(request, "lac/message.html", {"message": _("Recovery is in progress. This may take a few minutes."), "url": reverse("unix_index")})
    else:
        # Render the confirmation page
        return render(request, "lac/confirm.html", {"message": _("Please confirm the recovery of %(path)s.<br>The recovery will overwrite existing files.") % {"path": path}, "url_cancel": reverse("unix_index")})


@staff_member_required(login_url=settings.LOGIN_URL)
def enter_recovery_selector(request):
    request.session["redirection_after_selection"] = "recover_path"
    request.session["redirection_on_cancel"] = "unix_index"
    request.session["description"] = _("Please select the directory or file you want to restore. The restore will overwrite existing files.")
    request.session["allow_files"] = "True"
    request.session["current_directory"] = "/backups"
    return redirect("pick_folder")


@staff_member_required(login_url=settings.LOGIN_URL)
def test_mail(request):
    user_information = idm.ldap.get_user_information_of_cn(request.user.username)
    mail_adress = user_information.get("mail", "")
    if mail_adress == "" or mail_adress == None:
        return render(request, "lac/message.html", {"message": _("No email address found. Please define an email address in your user settings."), "url": reverse("user_settings")})
    message = email.send_mail([mail_adress], _("Test mail - Libre Workspace"), _("This is a test mail.\nYour mail settings seem to be correct."))
    if message != None:
        return render(request, "lac/message.html", {"message": _("Test mail could not be sent: <code>%(message)s</code>") % {"message": message}, "url": reverse("email_configuration")})
    return render(request, "lac/message.html", {"message": _("Test mail sent successfully. Please check your inbox."), "url": reverse("email_configuration")})


@staff_member_required(login_url=settings.LOGIN_URL)
def addons(request):
    addon_creator_url = reverse("addon_creator")
    overview = process_overview_dict({
        "heading": _("Local Addon Management"),
        "element_name": _("Addon"),
        "element_url_key": "id",
        "elements": unix.get_all_addon_modules(),
        "t_headings": [_("Name"), _("Description"), _("Author")],
        "t_keys": ["name", "description", "author"],
        "add_url_name": "add_addon",
        "delete_url_name": "remove_addon",
        "hint": _("<a href='%(addon_creator_url)s'>Create Add-On</a>") % {"addon_creator_url": addon_creator_url}
    })
    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def add_addon(request):
    if DISABLE_DANGEROUS_ADMIN_FUNCTIONS and request.user.username != "!superadmin":
        return message(request, _("This function has been disabled by the system administrator."), "addons")

    if request.method == "POST":
        file = request.FILES["file"]
        # Move the file to /tmp folder
        # Check if the file is a zip file
        if not file.name.endswith(".zip") and not file.name.endswith(".deb"):
            return message(request, _("The file must be a .zip or .deb file."), "add_addon")
        # Move the file to /tmp
        with open("/tmp/" + file.name, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        # Install the addon
        response = unix.install_addon("/tmp/" + file.name)
        if response != None:
            return message(request, _("The Addon could not be uploaded: %(response)s") % {"response": response}, "addons")
        appendix = ""
        if file.name.endswith(".deb"):
            appendix = _(" The Addon setup is currently running in the background and may take a few minutes.")
        return message(request, _("The Addon has been uploaded.") + appendix, "module_management")
    form = AddonForm()
    return render(request, "lac/generic_form.html", {"form": form, "heading": _("Add Add-On"), "hide_buttons_top": "True", "action": _("Upload"), "url": reverse("addons")})

@staff_member_required(login_url=settings.LOGIN_URL)
def remove_addon(request, addon_id):
    if unix.is_module_installed(addon_id):
        return message(request, _("The Addon cannot be uninstalled because it is still in use."), "addons")
    response = unix.uninstall_addon(addon_id)
    if response != None:
        return message(request, _("The Addon could not be uninstalled: <code>%(response)s</code>") % {"response": response}, "addons")
    return message(request, _("The Addon has been uninstalled."), "addons")


@staff_member_required(login_url=settings.LOGIN_URL)
def change_libre_workspace_name(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        unix.set_value("LIBRE_WORKSPACE_NAME", name)
        return message(request, _("The name has been changed."), "unix_index")
    form = forms.ChangeLibreWorkspaceNameForm()
    form.fields["name"].initial = unix.get_libre_workspace_name()
    return render(request, "lac/create_x.html", {"form": form, "heading": _("Change Libre Workspace Name"), "hide_buttons_top": "True", "url": reverse("unix_index")})


@staff_member_required(login_url=settings.LOGIN_URL)
def critical_system_configuration(request):
    return render(request, "unix/critical_system_configuration.html")


@staff_member_required(login_url=settings.LOGIN_URL)
def change_ip_address(request):
    if DISABLE_DANGEROUS_ADMIN_FUNCTIONS and request.user.username != "!superadmin":
        return message(request, _("This function has been disabled by the system administrator."), "critical_system_configuration")
    if request.method == "POST":
        ip = request.POST.get("ip", "")
        # Check if the ip is valid
        if not unix.is_valid_ip(ip):
            return message(request, _("The IP address is not valid."), "critical_system_configuration")
        unix.set_value("IP", ip)
        return message(request, _("The IP address has been changed."), "critical_system_configuration")
    form = forms.ChangeIpAdressForm()
    return render(request, "lac/generic_form.html", 
                  {"form": form, 
                   "heading": _("Change IP Address"),
                   "action": _("Change"),
                   "hide_buttons_top": "True", 
                   "url": reverse("critical_system_configuration"), 
                   "danger": "True",
                   "description": _("Please enter the new IP address of the server. The server will restart immediately afterwards.")})


@staff_member_required(login_url=settings.LOGIN_URL)
def change_master_password(request):
    if request.method == "POST":
        current_password = unix.get_administrator_password()
        if request.POST.get("old_password", "") != current_password:
            return message(request, _("The current password is incorrect."), "critical_system_configuration")
        if request.POST.get("new_password", "") != request.POST.get("new_password_repeat", ""):
            return message(request, _("The new passwords do not match."), "critical_system_configuration")
        password = request.POST.get("new_password", "")
        errors = unix.password_challenge(password)
        if errors == "":
            unix.change_master_password(password)
            return message(request, _("The master password has been changed. The server will restart shortly."), "critical_system_configuration")
        else:
            return message(request, _("The new password is not strong enough: %(errors)s") % {"errors": errors}, "critical_system_configuration")
    form = idm.forms.PasswordForm()
    return render(request, "lac/generic_form.html", 
                  {"form": form, 
                   "heading": _("Change Master Password"),
                   "action": _("Change"),
                   "hide_buttons_top": "True", 
                   "url": reverse("critical_system_configuration"), 
                   "danger": "True",
                   "description": _("Please enter the new master password. The master password will be changed immediately afterwards and the server will restart.")})


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
            unix.set_value("ADDITIONAL_MAIL_ADDRESSES_FOR_SYSTEM_MAILS", form.cleaned_data["additional_mail_addresses_for_system_mails"])
            unix.set_value("CPU_WARNING_THRESHOLD", form.cleaned_data["cpu_warning_threshold"])
            unix.set_value("RAM_WARNING_THRESHOLD", form.cleaned_data["ram_warning_threshold"])
            unix.set_value("DISK_WARNING_THRESHOLD", form.cleaned_data["disk_warning_threshold"])
            return message(request, _("Settings saved."), "system_configuration")
    form.fields["disable_nextcloud_user_administration"].initial = not unix.is_nextcloud_user_administration_enabled()
    form.fields["additional_mail_addresses_for_system_mails"].initial = unix.get_value("ADDITIONAL_MAIL_ADDRESSES_FOR_SYSTEM_MAILS", "")
    form.fields["cpu_warning_threshold"].initial = unix.get_value("CPU_WARNING_THRESHOLD", "80")
    form.fields["ram_warning_threshold"].initial = unix.get_value("RAM_WARNING_THRESHOLD", "80")
    form.fields["disk_warning_threshold"].initial = unix.get_value("DISK_WARNING_THRESHOLD", "90")

    ignored_domains_url = reverse("ignored_domains")
    content_above = f"<a href='{ignored_domains_url}' role='button'>{_('Manage ignored domains (E-Mail notifications)')}</a>"

    return render(request, "lac/generic_form.html", {"form": form, "heading": _("Miscellaneous Settings"), "action": _("Save"), "url": reverse("system_configuration"), "hide_buttons_top": "True", "content_above": content_above})


# API-Call
@staff_member_required(login_url=settings.LOGIN_URL)
def system_information(request):
    data = json.dumps(unix.get_system_information())
    return HttpResponse(data, content_type="application/json")


@staff_member_required(login_url=settings.LOGIN_URL)
def additional_services(request):
    if DISABLE_DANGEROUS_ADMIN_FUNCTIONS and request.user.username != "!superadmin":
        return message(request, _("This function has been disabled by the system administrator."), "system_configuration")
    if request.method == "POST":
        form = forms.AdditionalServicesForm(request.POST)
        if form.is_valid():
            unix.set_additional_services_control_files(form.cleaned_data["start_additional_services"], form.cleaned_data["stop_additional_services"])
            return message(request, _("Changes saved."), "system_configuration")
        return message(request, _("Error: Invalid input."), "additional_services")
    
    form = forms.AdditionalServicesForm()
    (start_additional_services, stop_additional_services) = unix.get_additional_services_control_files()
    form.fields["start_additional_services"].initial = start_additional_services
    form.fields["stop_additional_services"].initial = stop_additional_services
    return render(request, "lac/generic_form.html", {"form": form, "heading": _("Additional Services"), "action": _("Save"), "url": reverse("system_configuration"), "hide_buttons_top": "True", "description": _("Add valid Bash commands to be executed for starting and stopping your additional services. Do not use cd commands or similar.")})


@staff_member_required(login_url=settings.LOGIN_URL)
def update_libre_workspace(request):
    m = unix.update_libre_workspace()
    if m != None:
        return message(request, _("Libre Workspace could not be updated: <code>%(m)s</code>") % {"m": m}, "unix_index")
    return message(request, _("Libre Workspace is being updated. This may take a few minutes. Libre Workspace will be unavailable for a short time."), "unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def automatic_shutdown(request):
    form = forms.AutomaticShutdownForm()
    form.fields["enabled"].initial = unix.get_value("AUTOMATIC_SHUTDOWN_ENABLED", "False") == "True"
    form.fields["type"].initial = unix.get_value("AUTOMATIC_SHUTDOWN_TYPE", "Reboot")
    form.fields["time"].initial = unix.get_value("AUTOMATIC_SHUTDOWN_TIME", "02:00")
    form.fields["weekday"].initial = unix.get_value("AUTOMATIC_SHUTDOWN_WEEKDAY", "6")
    if request.method == "POST":
        form = forms.AutomaticShutdownForm(request.POST)
        if form.is_valid():
            unix.set_value("AUTOMATIC_SHUTDOWN_ENABLED", form.cleaned_data["enabled"])
            unix.set_value("AUTOMATIC_SHUTDOWN_TYPE", form.cleaned_data["type"])
            unix.set_value("AUTOMATIC_SHUTDOWN_WEEKDAY", form.cleaned_data["weekday"])
            
            if len(form.cleaned_data["time"]) != 5 or len(form.cleaned_data["time"].split(":")) != 2:
                return message(request, _("Error: The time format seems incorrect."), "automatic_shutdown")

            unix.set_value("AUTOMATIC_SHUTDOWN_TIME", form.cleaned_data["time"])
            print(form.cleaned_data["weekday"])
            return message(request, _("Settings saved."), "system_configuration")
        return message(request, _("Error: Invalid input."), "automatic_shutdown")
    return render(request, "lac/generic_form.html", {"form": form, "heading": _("Automatic Shutdown"), "action": _("Save"), "url": reverse("system_configuration"), "hide_buttons_top": "True", "description": _("Note: The process will only be executed within one hour of the configured time. If, for example, a simultaneously scheduled backup or update takes longer than one hour, the server will not be shut down/restarted.")})


@staff_member_required(login_url=settings.LOGIN_URL)
def get_system_data_for_support(request):
    unix.get_system_data_for_support()
    return message(request, _("System information has been collected and passwords removed. Click continue to download now."), "/static/support_data.zip")


@staff_member_required(login_url=settings.LOGIN_URL)
def update_module_now(request, module):
    m = unix.update_module(module)
    if m != None:
        return message(request, _("The module could not be updated: <code>%(m)s</code>") % {"m": m}, "unix_index")
    return message(request, _("The module is now being updated in the background. This may take a few minutes."), "unix_index")


@staff_member_required(login_url=settings.LOGIN_URL)
def desktop_settings(request):
    if DISABLE_DANGEROUS_ADMIN_FUNCTIONS and request.user.username != "!superadmin":
        return message(request, _("This function has been disabled by the system administrator."), "dashboard")
    form = forms.DesktopSettingsForm()
    if request.method == "POST":
        form = forms.DesktopSettingsForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["set_desktop_password"]
            unix.desktop_add_user(request.user.username, new_password, request.user.is_superuser)
            return message(request, _("Settings saved."), "dashboard")
        return message(request, _("Error: Invalid input."), "desktop_settings")
    

    return render(request, "lac/generic_form.html", {"form": form, "heading": _("Cloud Desktop"), "action": _("Apply"), "url": reverse("dashboard"), "hide_buttons_top": "True", "description": _("Note: The password is saved in plain text. The password is only required for password queries during use, for example for administrative tasks. The password is not required for login. The password can be deactivated again in the future when changing other user parameters for security reasons.")})


@staff_member_required(login_url=settings.LOGIN_URL)
def ignored_domains(request):
    overview_dict = {
        "element_name": _("Domain"),
        "heading": _("Ignored Domains"),
        "t_headings": [_("Domain")],
        "add_url_name": "add_ignored_domain",
        "delete_url_name": "remove_ignored_domain",
        "elements": unix.get_ignored_domains(),
        "back_url_name": "miscellaneous_settings",
        "content_above": "<p><strong>" + _("Ignored domains will not be checked for the online status. Therefore no warning mail will be sent if the domain is not reachable.") + "</strong></p>",
    }
    overview = process_overview_dict(overview_dict)
    return render(request, "lac/overview_x.html", {"overview": overview,})


@staff_member_required(login_url=settings.LOGIN_URL)
def add_ignored_domain(request):
    form = IgnoredDomainsForm(request.POST or None)
    if request.method == "POST":
        form = IgnoredDomainsForm(request.POST)
        if form.is_valid():
            unix.add_ignored_domain(form.cleaned_data["domain"])
            return message(request, _("The domain has been added to the ignored domains."), "ignored_domains")
        return message(request, _("Error: Invalid input."), "add_ignored_domain")
    return render(request, "lac/create_x.html", {"form": form, "heading": _("Add Ignored Domain"), "hide_buttons_top": "True", "url": reverse("ignored_domains")})


@staff_member_required(login_url=settings.LOGIN_URL)
def remove_ignored_domain(request, domain):
    unix.remove_ignored_domain(domain)
    return message(request, _("The domain has been removed from the ignored domains."), "ignored_domains")