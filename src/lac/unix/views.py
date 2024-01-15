from django.shortcuts import render
import unix.unix_scripts.unix as unix
import unix.forms as forms
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.models import User
from idm.idm import get_admin_user
import time


# Create your views here.
@staff_member_required
# System Management
def unix_index(request):
    backup_information = unix.get_borg_information_for_dashboard()
    disks_stats = unix.get_disks_stats()
    system_information = unix.get_system_information()
    update_information = unix.get_update_information()
    
    return render(request, "unix/system_management.html", {"backup_information": backup_information, "disks_stats": disks_stats, "system_information": system_information, "update_information": update_information})


@staff_member_required
def set_update_configuration(request):
    if request.method == "POST":
        software_modules = unix.get_software_modules()
        for module in software_modules:
            key = module["id"]
            configKey = key.upper() + "_AUTOMATIC_UPDATES"
            if request.POST.get(key, "") == "on":
                unix.set_value(configKey, "True")
            else:
                unix.set_value(configKey, "False")
        if request.POST.get("system", "") == "on":
            unix.set_value("SYSTEM_AUTOMATIC_UPDATES", "True")
        else:
            unix.set_value("SYSTEM_AUTOMATIC_UPDATES", "False")
        unix.set_value("UPDATE_TIME", request.POST.get("time", "02:00"))
    return redirect("unix_index")

@staff_member_required
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


@staff_member_required
def retry_backup(request):
    unix.retry_backup()
    time.sleep(1)
    return redirect("unix_index")


@staff_member_required
def update_system(request):
    unix.update_system()
    time.sleep(1)
    return redirect("unix_index")


@staff_member_required
def reboot_system(request):
    unix.reboot_system()
    return redirect("unix_index")


@staff_member_required
def shutdown_system(request):
    unix.shutdown_system()
    return redirect("unix_index")


@staff_member_required
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


@staff_member_required
def mount(request, partition):
    message = unix.mount(partition)
    if message != "":
        return HttpResponse("Fehler beim Einhängen: " + message)
    time.sleep(1)
    return redirect("data_management")


@staff_member_required
def umount(request, partition):
    message = unix.umount(partition)
    if message != "":
        return HttpResponse("Fehler beim Aushängen: " + message)
    time.sleep(1)
    return redirect("data_management")


@staff_member_required
def data_export(request):
    if request.method == "POST":
        partition = request.POST.get("partition-export", "")
    else:
        return HttpResponse("Fehler: POST Request erwartet")
    if partition == "":
        return HttpResponse("Fehler: Keine Partition ausgewählt")
    unix.export_data(partition)
    time.sleep(1)
    return redirect("data_management")


@staff_member_required
def abort_current_data_export(request):
    unix.abort_current_data_export()
    time.sleep(1)
    return redirect("data_management")


@staff_member_required
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
    
@staff_member_required
def data_import_2(request):
    if request.session["current_directory"] == "/":
        return HttpResponse("Fehler: Das Root-Verzeichnis kann nicht importiert werden")
    unix.import_folder_to_nextcloud_user(request.session["current_directory"], request.session["user_import"])
    time.sleep(1)
    return redirect("data_management")
    

# Session: current_directory*, redirection_after_selection, redirection_on_cancel, description
@staff_member_required
def pick_folder(request):
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
                request.session["current_directory"] = request.session["current_directory"] + "/" + request.POST.get("pick", "")
            request.session["current_directory"] = request.session["current_directory"].replace("//", "/")
        if request.POST.get("select", "") != "":
            return redirect(request.session["redirection_after_selection"])

    folder_list = unix.get_folder_list(request.session["current_directory"])
    file_list = unix.get_file_list(request.session["current_directory"])
    return render(request, "unix/pick_folder.html", {"description": description, "folder_list": folder_list, "current_directory": request.session["current_directory"], "file_list": file_list})


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
    message = request.POST.get("message", "").replace("\\n", "\n")
    attachment_path = request.POST.get("attachment_path", "")

    email = EmailMessage(subject=subject, body=message, from_email=settings.EMAIL_HOST_USER, to=[recipient])
    if attachment_path != "":
        email.attach_file(attachment_path)
    print("Sending email...")
    email.send()

    return HttpResponse("Mail send successfully")


@staff_member_required
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