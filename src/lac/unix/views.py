from django.shortcuts import render
import unix.unix_scripts.unix as unix
import unix.forms as forms
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.http import HttpResponse
import time


# Create your views here.
@staff_member_required
def unix_index(request):
    backup_information = unix.get_borg_information_for_dashboard()
    disks_stats = unix.get_disks_stats()
    system_information = unix.get_system_information()
    return render(request, "unix/system_management.html", {"backup_information": backup_information, "disks_stats": disks_stats, "system_information": system_information})

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
                request.session["current_directory"] = "/".join(request.session["current_directory"].split("/")[:-1])
            else:
                request.session["current_directory"] = request.session["current_directory"] + "/" + request.POST.get("pick", "")
            if request.session["current_directory"] == "":
                request.session["current_directory"] = "/"
            request.session["current_directory"] = request.session["current_directory"].replace("//", "/")
            print("picked!")
            print(request.session["current_directory"])

        if request.POST.get("select", "") != "":
            return redirect(request.session["redirection_after_selection"])

    folder_list = unix.get_folder_list(request.session["current_directory"])
    return render(request, "unix/pick_folder.html", {"description": description, "folder_list": folder_list, "current_directory": request.session["current_directory"]})