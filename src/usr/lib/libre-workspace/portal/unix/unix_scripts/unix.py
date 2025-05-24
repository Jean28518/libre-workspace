import os
import time
import subprocess
import json
import lac.settings as settings
import idm.ldap as ldap
import idm.idm as idm
import welcome.views
from app_dashboard.models import DashboardEntry
from django.urls import reverse
import requests
import unix.unix_scripts.utils as utils

# Change current directory to the directory of this script
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# If the config file does not exist, create it
if not os.path.isfile("/etc/libre-workspace/libre-workspace.conf"):
    os.system("touch /etc/libre-workspace/libre-workspace.conf")  
    

config = {}

def read_config_file():
    # Read the config file
    for line in open("/etc/libre-workspace/libre-workspace.conf"):
        if line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        # remove the " and ' characters from the outer ends of the string
        config[key.strip()] = value.strip("'\"\n ")

def write_config_file():
    # Write the config file
    with open("/etc/libre-workspace/libre-workspace.conf", "w") as f:
        for key, value in config.items():
            if value == "true" or value == "false" or value.isnumeric():
                f.write(f"{key}={value}\n")
            else:
                f.write(f"{key}=\"{value}\"\n")

def get_value(key, default=""):
    read_config_file()
    # Get the value of a key from the config file
    if key in config:
        return config[key]
    else:
        return default
    
def set_value(key, value):
    read_config_file()
    value = str(value)
    # Set the value of a key in the config file
    if value != "":
        config[key] = value
    elif key in config:
        del config[key]
    print(f"Setting {key} to {value}")
    write_config_file()

# rv["backup_status"] can be one of the following:
# ok
# last_backup_failed
# running
# recovery_running
# deactivated
# not_configured
# no_backup_yet
def get_borg_information_for_dashboard():
    rv = {} # return value
    rv["compressed_size_of_all_backups"] = 0

    # Get the compressed size of all backups
    if os.path.isfile("/var/lib/libre-workspace/portal/history/borg_info"):
        lines = open("/var/lib/libre-workspace/portal/history/borg_info").readlines()
        for line in lines:
            if line.startswith("All archives:"):
                size = line[-15:-1].strip()
                rv["compressed_size_of_all_backups"] = size
    
    rv["encrypted"] = get_value("BORG_ENCRYPTION") == "true"

    rv["backup_status"] = "ok"

    # Get all archives
    rv["archives"] = []
    if os.path.isfile("/var/lib/libre-workspace/portal/history/borg_list"):
        lines = open("/var/lib/libre-workspace/portal/history/borg_list").readlines()
        for line in lines:
            rv["archives"].append(line.strip())
    # Sort archives by date
    rv["archives"] = sorted(rv["archives"], key=lambda k: k[0:10], reverse=True)

    if os.path.ismount("/backups"):
        rv["backup_mounted"] = "True"
    else:
        rv["backup_mounted"] = "False"


    backup_history = []
    date_max = "1970-01-01"
    # Get all files in the history directory
    for file in os.listdir("/var/lib/libre-workspace/portal/history/"):
        if file.startswith("borg_errors_"):
            entry = {}
            # Get the date from the filename
            date = file[12:-4]
            # Get the error message from the file
            error = open(f"/var/lib/libre-workspace/portal/history/{file}").read()
            if error.strip() == "":
                entry["success"] = True
            else:
                entry["success"] = False
            if date > date_max:
                date_max = date
            entry["date"] = date
            entry["error"] = error
            backup_history.append(entry)
    # Sort backup_history by date
    backup_history = sorted(backup_history, key=lambda k: k['date'], reverse=True)
    rv["backup_history"] = backup_history

    for entry in rv["backup_history"]:
        if entry["date"] == date_max:
            rv["last_backup"] = entry
            if not rv["last_backup"]["success"]:
                rv["backup_status"] = "last_backup_failed"
    
    if utils.is_backup_running():
        rv["backup_status"] = "running"
    
    if os.path.isfile("/var/lib/libre-workspace/portal/recovery_running"):
        rv["backup_status"] = "recovery_running"

    # If file "deactivated" exists, set backup status to "deactivated"
    if os.path.isfile("backup_disabled"):
        rv["backup_status"] = "deactivated"

    # If the repository is not configured, set backup status to "not_configured"
    if get_value("BORG_REPOSITORY") == "":
        rv["backup_status"] = "not_configured"

    # If everything is okay but no backup has been made yet, set backup status to "no_backup_yet"
    if rv["backup_status"] == "ok" and len(rv["backup_history"]) == 0:
        rv["backup_status"] = "no_backup_yet"

    return rv


# Returns true if we are running on a ubuntu system
def is_system_ubuntu():
    string = subprocess.getoutput("cat /etc/os-release")
    return "ubuntu" in string.lower()


def get_public_key():
    # Get the public key of the root user
    if os.path.isfile("/var/lib/libre-workspace/portal/id_rsa.pub"):
        return open("/var/lib/libre-workspace/portal/id_rsa.pub").read()
    else:
        return "Error: Public key of root user not found."
    
def get_trusted_fingerprint():
    # Get the trusted fingerprint
    if os.path.isfile("trusted_fingerprints"):
        return open("trusted_fingerprints").read()
    else:
        return ""

def set_trusted_fingerprint(fingerprint):
    # Set the trusted fingerprint
    with open("trusted_fingerprints", "w") as f:
        f.write(fingerprint)

def retry_backup():
    read_config_file()
    # If the backup is currently running, exit
    if utils.is_backup_running():
        return
    # If the backup is deactivated, exit
    if os.path.isfile("/var/lib/libre-workspace/portal/backup_disabled"):
        return
    # If the repository is not configured, exit
    if config["BORG_REPOSITORY"] == "":
        return
    # Remove the history file of today
    date = time.strftime("%Y-%m-%d")
    if os.path.isfile(f"/var/lib/libre-workspace/portal/history/borg_errors_{date}.log"):
        os.remove(f"/var/lib/libre-workspace/portal/history/borg_errors_{date}.log")
    trigger_cron_service()

def is_backup_enabled():
    # Return True if backup is enabled, False if backup is disabled
    return not os.path.isfile("/var/lib/libre-workspace/portal/backup_disabled")

def set_backup_enabled(enabled):
    # Enable or disable the backup
    if enabled:
        if os.path.isfile("/var/lib/libre-workspace/portal/backup_disabled"):
            os.remove("/var/lib/libre-workspace/portal/backup_disabled")
    else:
        if not os.path.isfile("/var/lib/libre-workspace/portal/backup_disabled"):
            os.system("touch /var/lib/libre-workspace/portal/backup_disabled")


def get_disks_stats():
    return utils.get_disks_stats()

def get_system_information():
    # Get hostname, ram usage, cpu usage, uptime, os version
    rv = {}
    rv["lw_name"] = get_libre_workspace_name()
    rv["lw_version"] = get_libre_workspace_version()
    rv["hostname"] = subprocess.getoutput("hostname")

    v = utils.get_ram_usage()
    rv["total_ram"] = v["total_ram"]
    rv["ram_usage"] = v["ram_usage"]
    rv["ram_percent"] = v["ram_percent"]

    rv["cpu_usage_percent"] = utils.get_cpu_usage()

    rv["uptime"] = subprocess.getoutput("uptime -p").replace("up", "").replace("minutes", "Minuten").replace("hours", "Stunden").replace("days", "Tage").replace("weeks", "Wochen").replace("months", "Monate").replace("years", "Jahre")
    rv["uptime"] = rv["uptime"].replace("min", "Min").replace("hour", "Stunde").replace("day", "Tag").replace("week", "Woche").replace("month", "Monat").replace("year", "Jahr")
    rv["uptime_in_seconds"] = int(subprocess.getoutput("cat /proc/uptime").split(" ")[0].split(".")[0])
    rv["os"] = subprocess.getoutput("cat /etc/os-release").split("\n")[0].split("=")[1].strip('"')

    rv["new_libre_workspace_version"] = is_libre_workspace_update_available()


    rv["update_information"] = f"{get_upgradable_packages()} Pakete können aktualisiert werden." if get_upgradable_packages() > 0 else "Das System ist auf dem neuesten Stand."
    if os.path.exists("/var/lib/libre-workspace/portal/history/update.log") and not is_update_currently_running():
        rv["last_update_log"] = open("/var/lib/libre-workspace/portal/history/update.log").read().replace("\n", " <br> ")
    if is_update_currently_running():
        rv["update_information"] = "Das System wird gerade aktualisiert..."
    return rv


def get_upgradable_packages():
    if not os.path.isfile("/var/lib/libre-workspace/portal/upgradable_packages"):
        return 0
    return int(subprocess.getoutput("cat /var/lib/libre-workspace/portal/upgradable_packages | wc -l")) -1


def is_update_currently_running():
    return os.path.isfile("/var/lib/libre-workspace/portal/update_running")


def trigger_cron_service():
    # If the run_service file exists, remove it and run service immediately
    os.system("touch /var/lib/libre-workspace/portal/run_service")

def update_system():
    # If the update is currently running, exit
    if os.path.isfile("/var/lib/libre-workspace/portal/update_system"):
        return
    os.system("touch /var/lib/libre-workspace/portal/update_system")
    trigger_cron_service()
    


def reboot_system():
    os.system("/sbin/shutdown -r now")


def shutdown_system():
    os.system("/sbin/shutdown -h now")


def start_all_services():
    subprocess.Popen(["/usr/bin/bash", "start_services.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/", env=get_env_from_unix_conf())


def stop_all_services():
    subprocess.Popen(["/usr/bin/bash", "stop_services.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/", env=get_env_from_unix_conf())


def escape_bash_characters(string, also_escape_paths=True):
    if also_escape_paths:
        string = string.replace("/", "").replace("\\", "").replace(".", "")
    return string.replace(";", "").replace("&", "").replace("|", "").replace(">", "").replace("<", "").replace("$", "")


def get_partitions():
    if is_system_ubuntu():
        data = subprocess.getoutput("lsblk -aJ")
    else:
        data = subprocess.getoutput("lsblk -AJ")
    data = json.loads(data)

    partitions = []
    for item in data["blockdevices"]:
        if "children" in item:
            for child in item["children"]:
                partition = {}
                partition["name"] = child["name"]
                partition["size"] = child["size"]
                partition["mountpoint"] = None
                partition["under1G"] = partition["size"].lower().endswith("m") or partition["size"].lower().endswith("k")
                if "mountpoints" in child:
                    partition["mountpoint"] = child["mountpoints"][0]
                partitions.append(partition)
    return partitions


def mount(partition):
    partition = escape_bash_characters(partition)
    message = subprocess.getoutput(f"mkdir -p /mnt/{partition}")
    if message != "":
        return message
    return subprocess.getoutput(f"mount /dev/{partition} /mnt/{partition}")


def umount(partition):
    partition = escape_bash_characters(partition)
    message = subprocess.getoutput(f"umount /mnt/{partition}")
    subprocess.getoutput(f"rmdir /mnt/{partition}")
    return message


# Exports all important files of the whole system to the specified filepath
def export_data(filepath):
    filepath = escape_bash_characters(filepath, False)
    if os.path.exists("export_data"):
        return "Backup already running"
        
    os.system(f"echo '{filepath}' > export_data")
    trigger_cron_service()
    return


def get_data_export_status():
    if os.path.isfile("export_running"):
        return "running"
    return "not_running"


def abort_current_data_export():
    if os.path.isfile("export_running"):
        os.system("rm export_running")
        os.system("rm export_data")
        os.system("pkill do_data_export.sh")
        os.system("bash start_service.sh")
    return


def get_rsync_history():
    if not os.path.isfile("/var/lib/libre-workspace/portal/history/rsync.log"):
        return ""
    rsync_history = open("/var/lib/libre-workspace/portal/history/rsync.log").read().replace("\n", "<br>")
    return rsync_history

def is_nextcloud_installed():
    return os.path.isfile(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/config/config.php")

# Format: [{"name": "user1", "path": "/path/to/user1"}, {"name": "user2", "path": "/path/to/user2"}]
def get_nextcloud_user_directories():
    if not os.path.isfile(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/config/config.php"):
        return []
    nextcloud_config_file = open(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/config/config.php").readlines()
    for line in nextcloud_config_file:
        if "datadirectory" in line:
            nextcloud_data_directory = line.split("=>")[1].strip().replace("'", "").strip('"').strip(",")
            break
    nextcloud_users = []
    for user in os.listdir(nextcloud_data_directory):
        if not "appdata" in user and not user == "files_external" and not user == "__groupfolders" and os.path.isdir(nextcloud_data_directory + "/" + user):
            nextcloud_users.append({"name": user, "path": nextcloud_data_directory + "/" + user + "/files"})

    # Translate the objectGUID to the username for each nextcloud user
    ldap_users = ldap.ldap_get_all_users()
    for ldap_user in ldap_users:
        for nextcloud_user in nextcloud_users:
            # Match only the last 8 characters of the objectGUID with the last 8 characters of the username, because the objectGUID of ldap_users is slightly different from the username of nextcloud_users
            if ldap_user["guid"].upper()[-8:-1] == nextcloud_user["name"].replace("-", "")[-8:-1]:
                nextcloud_user["name"] = ldap_user["cn"]

    return nextcloud_users


def get_folder_list(path):
    path = escape_bash_characters(path, False)
    if not os.path.isdir(path):
        return []
    folders = []
    for folder in os.listdir(path):
        if os.path.isdir(path + "/" + folder):
            folders.append(folder)
    folders.sort()
    return folders


def get_file_list(path):
    path = escape_bash_characters(path, False)
    if not os.path.isdir(path):
        return []
    files = []
    for folder in os.listdir(path):
        if os.path.isfile(path + "/" + folder):
            files.append(folder)
    files.sort()
    return files

def get_directory_above(path):
    path = "/".join(path.split("/")[:-1])
    if path == "":
            path = "/"
    return path


def import_folder_to_nextcloud_user(folder_import, nextcloud_user_folder):
    os.environ["NEXTCLOUD_USER_FOLDER"] = nextcloud_user_folder
    os.environ["FOLDER_IMPORT"] = folder_import
    os.environ["NEXTCLOUD_INSTALLATION_DIRECTORY"] = settings.NEXTCLOUD_INSTALLATION_DIRECTORY
    os.system("bash import_folder_to_nextcloud_user.sh &")


def nextcloud_import_process_running():
    return os.path.isfile("nextcloud_import_process_running")


def abort_current_nextcloud_import():
    os.system("rm nextcloud_import_process_running")
    os.system("pkill import_folder_to_nextcloud_user.sh")

def is_matrix_installed():
    return os.path.isdir("/root/matrix/")


def is_jitsi_installed():
    return os.path.isdir("/root/jitsi/")


def is_collabora_installed():
    return os.path.isdir("/root/collabora/")


def is_onlyoffice_installed():
    return os.path.isdir("/root/onlyoffice/")


def is_desktop_installed():
    return os.path.isdir("/root/desktop/")


def get_software_modules():
    modules = []
    modules.append({ "id": "samba_dc", "name": "Samba DC (Zentrale Nutzerverwaltung)", "automaticUpdates": get_value("SAMBA_DC_AUTOMATIC_UPDATES", "False") == "True", "installed": is_samba_dc_installed() })
    modules.append({ "id": "nextcloud", "name": "Nextcloud", "automaticUpdates": get_value("NEXTCLOUD_AUTOMATIC_UPDATES", "False") == "True", "installed": is_nextcloud_installed() })
    modules.append({ "id": "matrix", "name": "Matrix", "automaticUpdates": get_value("MATRIX_AUTOMATIC_UPDATES", "False") == "True", "installed": is_matrix_installed() })
    modules.append({ "id": "jitsi", "name": "Jitsi", "automaticUpdates": get_value("JITSI_AUTOMATIC_UPDATES", "False") == "True", "installed": is_jitsi_installed() })
    modules.append({ "id": "collabora", "name": "Collabora", "automaticUpdates": get_value("COLLABORA_AUTOMATIC_UPDATES", "False") == "True", "installed": is_collabora_installed() })
    modules.append({ "id": "onlyoffice", "name": "OnlyOffice", "automaticUpdates": get_value("ONLYOFFICE_AUTOMATIC_UPDATES", "False") == "True", "installed": is_onlyoffice_installed() })
    modules.append({ "id": "desktop", "name": "Cloud Desktop", "automaticUpdates": get_value("DESKTOP_AUTOMATIC_UPDATES", "False") == "True", "installed": is_desktop_installed() })
    modules.append({ "id": "xfce", "name": "XFCE", "automaticUpdates": get_value("XFCE_AUTOMATIC_UPDATES", "False") == "True", "installed": is_xfce_installed() })
    
    for module in modules:
        module["scriptsFolder"] = f"{module['id']}"

    # Get addons:
    addons = get_all_addon_modules()
    for addon in addons:
        addon["installed"] = is_module_installed(addon["id"])
        addon["automaticUpdates"] = get_value(f"{addon['id'].upper().replace('-', '_')}_AUTOMATIC_UPDATES", "False") == "True"
        addon["scriptsFolder"] = f"/usr/lib/libre-workspace/modules/{addon['id']}"
        modules.append(addon)

    return modules


def desktop_add_user(username, password, admin_status):
    """
    Only works if the desktop module is installed.
    Adds a user to the desktop module. If user exists, it updates the user configuration.
    Password can be empty. In these cases a random password will be generated.
    """
    if not is_desktop_installed():
        return
    
    if admin_status:
        admin_status = "1"
    else:
        admin_status = "0"
    
    subprocess.Popen(["/usr/bin/bash", "/usr/lib/libre-workspace/modules/desktop/administration/add_user.sh", username, password, admin_status], cwd="desktop/", env=get_env_sh_variables())


def desktop_remove_user(username):
    """
    Removes a user from the desktop module.
    """
    if not is_desktop_installed():
        return
    
    subprocess.Popen(["/usr/bin/bash", "/usr/lib/libre-workspace/modules/desktop/administration/remove_user.sh", username], cwd="desktop/", env=get_env_sh_variables())

def update_module(module_id):
    """
    Works for addons and modules.
    """
    software_modules = get_software_modules()

    if module_id in ["system", "xfce"]:
        update_system()
        return
    
    if module_id == "libre_workspace":
        update_libre_workspace()
        return

    for module in software_modules:
        if module["id"] == module_id:
            if module["installed"]:
                # Get absolute path for the module
                module_path = get_module_path(module_id)
                env = get_env_sh_variables()
                p = subprocess.Popen(["/usr/bin/bash", f"update_{module_id}.sh"], cwd=module_path, env=env)
                return
            else:
                return "Error: Module not installed."
    return "Error: Module not found."


# We determine if a module is installed by checking if the module's directory exists in the root directory
def is_module_installed(module_or_addon: str):
    """ 
    If this is True, then the module or addon is really installed into the server.
    """
    return os.path.isdir(f"/root/{module_or_addon}")


def get_update_history():
    history = []
    for file in os.listdir("/var/lib/libre-workspace/portal/history/"):
        if file.startswith("update-"):
            entry = {}
            entry["date"] = file[7:-4]
            entry["content"] = open(f"/var/lib/libre-workspace/portal/history/{file}").read().replace("\n", "<br>")
            history.append(entry)
    history = sorted(history, key=lambda k: k['date'], reverse=True)
    return history


def get_update_information():
    update_information = {}
    update_information["software_modules"] = get_software_modules()
    update_information["software_modules"].insert(0, {"id": "system", "name": "System", "installed": True, "automaticUpdates": get_value("SYSTEM_AUTOMATIC_UPDATES", "False") == "True"})
    update_information["software_modules"].insert(0, {"id": "libre_workspace", "name": "Libre Workspace", "installed": True, "automaticUpdates": get_value("LIBRE_WORKSPACE_AUTOMATIC_UPDATES", "False") == "True"})
    update_information["update_time"] = get_value("UPDATE_TIME", "02:00")
    update_information["update_history"] = get_update_history()
    print(update_information)
    return update_information

def get_env_sh_variables():
    return_value = {}
    if not os.path.isfile("/etc/libre-workspace/libre-workspace.env"):
        return return_value
    for line in open("/etc/libre-workspace/libre-workspace.env").readlines():
        if line.strip() != "":
            if line.strip().startswith("#"):
                continue
            line = line.replace("export ", "")
            # Split the first = sign
            key, value = line.split("=", 1)
            return_value[key] = value.strip().strip('"').strip()
    return return_value

def get_env_from_unix_conf():
    read_config_file()
    return config


def get_module_path(module_name):
    if os.path.isdir(f"/usr/lib/libre-workspace/modules/{module_name}"):
        return f"/usr/lib/libre-workspace/modules/{module_name}"
    return module_name


# Also "installs" addons
def setup_module(module_name):
    module_path = get_module_path(module_name)
    # Check if module is an addon:
    if "addon" in module_path:
        # Add the entry to the /etc/hosts file
        addon = get_config_of_addon(module_name)
        urls = addon.get("url", "").split(",")      
        for url in urls:
            domain = get_env_sh_variables().get("DOMAIN", "")
            ip = get_env_sh_variables().get("IP", "")   
            os.system(f"echo \"{ip} {url}.{domain}\" >> /etc/hosts")
            
            
            # Add the entry to the DNS server
            if settings.AUTH_LDAP_ENABLED:
                admin_password = get_env_sh_variables().get("ADMIN_PASSWORD", "")
                # Run this command: samba-tool dns add la.$DOMAIN $DOMAIN matrix A $IP -U administrator%$ADMIN_PASSWORD
                os.system(f"samba-tool dns add la.{domain} {domain} {url} A {ip} -U administrator%{admin_password}")
        

    # Check if path extists: module_path/setup_module_name.sh
    if os.path.isfile(f"{module_path}/setup_{module_name}.sh"):
        process = subprocess.Popen(["/usr/bin/bash", f"setup_{module_name}.sh"], cwd=f"{module_path}/", env=get_env_sh_variables())
    else:
        return "WARNING: Setup script not found! If you are in a development environment, thats okay. If you are in a production environment, please check your installation."


def remove_module(module_name):
    """
    Uninstalls the module from the server.)
    """
    module_path = get_module_path(module_name)

    if "addon" in module_path:
        # Remove the entry from the /etc/hosts file
        addon = get_config_of_addon(module_name)
        urls = addon.get("url", "").split(",")
        domain = get_env_sh_variables().get("DOMAIN", "")
        if domain == "":
            return "No domain found in the libre-workspace.env file. Please check the /etc/libre-workspace/libre-workspace.env file."
        for url in urls:
            ip = get_env_sh_variables().get("IP", "")   
            os.system(f"sed -i '/{url}.{domain}/d' /etc/hosts")

            # Remove the entry from the DNS server
            if settings.AUTH_LDAP_ENABLED:
                admin_password = get_env_sh_variables().get("ADMIN_PASSWORD", "")
                # Run this command: samba-tool dns delete la.$DOMAIN $DOMAIN matrix A $IP -U administrator%$ADMIN_PASSWORD
                os.system(f"samba-tool dns delete la.{domain} {domain} {module_name} A {ip} -U administrator%{admin_password}")
    
    # Check if path extists: module_name/remove_module_name.sh
    if os.path.isfile(f"{module_path}/remove_{module_name}.sh"):
        process = subprocess.Popen(["/usr/bin/bash", f"remove_{module_name}.sh"], cwd=f"{module_path}/", env=get_env_sh_variables())
    else:
        return "WARNING: Remove script not found! If you are in a development environment, thats okay. If you are in a production environment, please check your installation."
    

def get_online_office_module():
    if is_collabora_installed():
        return "collabora"
    if is_onlyoffice_installed():
        return "onlyoffice"
    return None


def mount_backups():
    process = subprocess.Popen(["/usr/bin/bash", "mount_backups.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/", env=get_env_from_unix_conf())
    time.sleep(5)
    if process.returncode != None and process.returncode != 0:
        return "Error: Mounting backups failed: " + str(process.stdout) + " " + str(process.stderr)


def umount_backups():
    process = subprocess.Popen(["/usr/bin/bash", "umount_backups.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/", env=get_env_from_unix_conf())
    time.sleep(1)
    if process.returncode != None and process.returncode != 0:
        return "Error: Umounting backups failed: " + str(process.stdout) + " " + str(process.stderr)
    

# This function needs the location in the backup to recover and the location to recover to
# Example: full_path_to_backup = "/backup/2021-01-01_12-00-00", full_path_to_recover_to = "/mnt/restore"
def recover_file_or_dir(full_path_to_backup):
    process = subprocess.Popen(["/usr/bin/bash", "recover_path.sh", full_path_to_backup], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/", env=get_env_from_unix_conf(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    if process.returncode != None and process.returncode != 0:
        return "Error: Recovering file or directory failed: " + str(process.stdout.read()) + " " + str(process.stderr.read())
    

def is_path_a_file(path):
    return os.path.isfile(path)


# Returns array with all configs
def get_all_addon_modules():
    # Get all folders in the addons directory
    addons = []
    for folder in os.listdir("/usr/lib/libre-workspace/modules/"):
        if os.path.isdir(f"/usr/lib/libre-workspace/modules/{folder}") and os.path.isfile(f"/usr/lib/libre-workspace/modules/{folder}/{folder}.conf"):
            addons.append(get_config_of_addon(folder))
    return addons

addon_config_cache = {}
def get_config_of_addon(addon):
    if addon in addon_config_cache.keys():
        return addon_config_cache[addon]
    # Read the config file of the addon
    config = {}
    for line in open(f"/usr/lib/libre-workspace/modules/{addon}/{addon}.conf"):
        if line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        # remove the " and ' characters from the outer ends of the string
        config[key.strip()] = value.strip("'\"\n ")
        # Get icon file format
    for file in os.listdir(f"/usr/lib/libre-workspace/modules/{addon}"):
        if file.endswith(".png") or file.endswith(".svg") or file.endswith(".jpg") or file.endswith(".webp"):
            config["icon_file_format"] = file.split(".")[-1]
    addon_config_cache[addon] = config
    return config


def install_addon(path_to_file):
    # Remove the old folder of the addon if it exists
    if os.path.exists("/tmp/lw-addons/"):
        os.system("rm -r /tmp/lw-addons/")
    os.system("mkdir -p /tmp/lw-addons/")

    # if the file is a .zip file, unzip it to /tmp/lw-addons/
    if path_to_file.endswith(".zip"):
        os.system(f"unzip '{path_to_file}' -d /tmp/lw-addons/")
    # Otherwise copy the file to /tmp/lw-addons/
    elif path_to_file.endswith(".deb"):
        os.system(f"cp '{path_to_file}' /tmp/lw-addons/")
    else:
        # If the file is not a .zip, .tar.gz, .tar.xz or .deb file, return an error
        return "Error: File format not supported. Please use a .zip or .deb file."

    # Check if .deb files are inside the addon folder (recursive) we can do this with "find"
    deb_files = os.popen(f"find /tmp/lw-addons/ -name '*.deb'").read().strip().split("\n")
    if len(deb_files) > 0:
        # Install the .deb file(s)
        for deb_file in deb_files:
            subprocess.Popen(["apt", "install", deb_file, "-y"])
            time.sleep(3)  # Wait to ensure the installation is progressed to postinstallation scripts
    else: 
        # Otherwise the old method (deprecated):
        addon_id = os.listdir("/tmp/lw-addons/")[0]
        os.system(f"rm -r '/usr/lib/libre-workspace/modules/{addon_id}'")
        os.system(f"mv /tmp/lw-addons/{addon_id} /usr/lib/libre-workspace/modules/")
    
    os.system(f"rm {path_to_file}")
    os.system(f"rm -r /tmp/lw-addons/")
    # Ensure that the addon cache is cleared
    addon_config_cache.clear()
    update_static_module_icons()


def update_static_module_icons():
    """Updates the static icons of all addons in the static folder."""
    addons = get_all_addon_modules()
    for addon in addons:
        addon_id = addon["id"]
        for file in os.listdir(f"/usr/lib/libre-workspace/modules/{addon_id}"):
            if file.endswith(".png") or file.endswith(".svg") or file.endswith(".jpg") or file.endswith(".webp"):
                # Copy the image file to the static folder
                os.system(f"cp /usr/lib/libre-workspace/modules/{addon_id}/{file} /usr/lib/libre-workspace/portal/lac/static/lac/icons/{addon_id}.{file.split('.')[-1]}")
                # Also copy to /var/www/libre-workspace-static/lac/icons/ (that is the folder where the static files are served from)
                os.system(f"cp /usr/lib/libre-workspace/modules/{addon_id}/{file} /var/www/libre-workspace-static/lac/icons/{addon_id}.{file.split('.')[-1]}")
                os.system(f"chown www-data:www-data /var/www/libre-workspace-static/lac/icons/{addon_id}.{file.split('.')[-1]}")
                os.system(f"chmod 644 /var/www/libre-workspace-static/lac/icons/{addon_id}.{file.split('.')[-1]}")


def uninstall_addon(addon_id):
    """"
    Removes the folder of the addon. Don't uninstall the addon if it is currently installed into the server.
    """
    addon_information = get_config_of_addon(addon_id)

    # Check if the addon is installed as a .deb package via dpkg. It has to be named like "libre-workspace-module-<addon_id>"
    if os.system(f"dpkg -l | grep libre-workspace-module-{addon_id}") == 0:
        # If it is installed, remove it via apt
        os.system(f"apt remove libre-workspace-module-{addon_id} -y")
    else:
        # Remove it the old way (deprecated):
        os.system(f"rm -r /usr/lib/libre-workspace/modules/{addon_id}")

    os.system(f"rm /usr/lib/libre-workspace/portal/lac/static/lac/icons/{addon_id}.*")
    os.system(f"rm /var/www/libre-workspace-static/lac/icons/{addon_id}.*")
    # Remove the entry from the AppDashboardEntry table in the database
    DashboardEntry.objects.filter(title=addon_information["name"], is_system=True).delete()


def get_all_installed_nextcloud_addons():
    """"
    Returns a list of all installed nextcloud addons.
    """
    addons = []
    if not is_nextcloud_installed():
        return addons
    for folder in os.listdir(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/apps"):
        if os.path.isdir(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/apps/" + folder):
            addons.append(folder)
    return addons


def restart_libre_workspace_portal():
    # Only run this command one second after the function was called to ensure that the response is sent to the client before the server restarts
    subprocess.Popen("sleep 1; systemctl restart libre-workspace-portal",shell=True)


def get_libre_workspace_name():
    domain = get_env_sh_variables().get("DOMAIN", "")
    return get_value(f"LIBRE_WORKSPACE_NAME", f"{domain} - Libre Workspace")


def set_libre_workspace_name(name):
    set_value("LIBRE_WORKSPACE_NAME", name)


def get_libre_workspace_version():
    # Get the version of installed libre-workspace.deb:
    output = subprocess.getoutput("dpkg -s libre-workspace-portal | grep Version")
    if "Version" in output:
        return output.split(":")[1].strip()
    else:
        return "?"
    

def change_master_password(password):
    # Update password for the administrator user in the LDAP server
    os.system("samba-tool user setpassword Administrator --newpassword=" + password)

    # Update the password of the django admin user, if present
    idm.change_superuser_password(password)
        
    # Update the password of the systemv (linux) user by changing the password in the /etc/shadow file
    os.system("pam-auth-update --force --disable krb5")
    os.system(f"echo \"systemv:{password}\" | chpasswd")
    os.system("pam-auth-update --force --enable krb5")

    # Update the password in the /etc/libre-workspace/libre-workspace.env file
    os.system(f"sed -i 's/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=\"{password}\"/g' /etc/libre-workspace/libre-workspace.env")

    # Change the configured bind password in /etc/libre-workspace/portal/portal.conf
    os.system(f"sed -i 's/AUTH_LDAP_BIND_PASSWORD=.*/AUTH_LDAP_BIND_PASSWORD=\"{password}\"/g' /etc/libre-workspace/portal/portal.conf")

    # Update the password in apps like nextcloud, matrix.
    # We are doing this by running the update_env.sh scripts in the specific folders.
    env = get_env_sh_variables()
    for module  in get_software_modules():
        if module["installed"]:
            subprocess.Popen(["/usr/bin/bash", "update_env.sh"], cwd=module["scriptsFolder"] + "/", env=env).wait()

    # Restart the whole server to ensure that the new password is used everywhere.
    reboot_system()


def change_ip(ip):
    # Get old ip
    old_ip = get_env_sh_variables().get("IP", "")

    # Change the IP in the /etc/libre-workspace/libre-workspace.env file
    os.system(f"sed -i 's/IP=.*/IP=\"{ip}\"/g' /etc/libre-workspace/libre-workspace.env")

    # Change the IP in the /etc/hosts file
    os.system(f"sed -i 's/{old_ip}/{ip}/g' /etc/hosts")

    # Change the IP-Adress in /etc/resolv.conf
    os.system("chattr -i -a /etc/resolv.conf")
    os.system(f"sed -i 's/{old_ip}/{ip}/g' /etc/resolv.conf")
    os.system("chattr +i +a /etc/resolv.conf")


    # Change the IP in the DNS server of samba
    domain = get_env_sh_variables().get("DOMAIN", "")
    admin_password = get_env_sh_variables().get("ADMIN_PASSWORD", "")

    # This only works if the domain of samba-ac-dc is the same as the real domain.
    # (See SHORTEND_DOMAIN in setup_samba_ad_dc.sh)
    for subdomain in welcome.views.subdomains:
        os.system(f"samba-tool dns update {subdomain}.{domain} {domain} {ip} A -U administrator%{admin_password}")
    for addon in get_all_addon_modules():
        os.system(f"samba-tool dns update {addon['url']}.{domain} {domain} {ip} A -U administrator%{admin_password}")

    # Change the IP in apps like nextcloud, matrix and also in the addons.
    env = get_env_sh_variables()
    for module  in get_software_modules():
        if module["installed"]:
            subprocess.Popen(["/usr/bin/bash", "update_env.sh"], cwd=module["scriptsFolder"] + "/", env=env).wait()

    # Change all old ips with the new ip in /etc/caddy/Caddyfile
    os.system(f"sed -i 's/{old_ip}/{ip}/g' /etc/caddy/Caddyfile")

    # Change all old ips with the new ip in /usr/lib/libre-workspace/portal/welcome/templates/welcome/access_rendered.html
    os.system(f"sed -i 's/{old_ip}/{ip}/g' /usr/lib/libre-workspace/portal/welcome/templates/welcome/access_rendered.html")

    # Restart the whole server to ensure that the new IP is used everywhere.
    reboot_system()


def is_valid_ip(ip):
    # Check if the ip is valid
    try:
        ip = ip.split(".")
        if len(ip) != 4:
            return False
        for i in ip:
            if int(i) < 0 or int(i) > 255:
                return False
    except:
        return False
    return True


def get_administrator_password():
    return get_env_sh_variables().get("ADMIN_PASSWORD", "")


def password_challenge(password):
    """Returns a message if the password is not valid. If the password is valid, it returns ""."""
    message = ""
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
    return message


def is_nextcloud_user_administration_enabled():
    # Check if @lw_usersettings { is in the Cadddyfile
    caddyfile = open("/etc/caddy/Caddyfile").read()
    return not ("@lw_usersettings {" in caddyfile)


def disable_nextcloud_user_administration():
    if not is_nextcloud_user_administration_enabled():
        return
    domain = get_env_sh_variables().get("DOMAIN", "")
    # Open caddyfile lines and add the handler line after the line where cloud. is in
    caddyfile = open("/etc/caddy/Caddyfile").read()
    caddyfile = caddyfile.split("\n")
    for i, line in enumerate(caddyfile):
        if "cloud." in line:
            caddyfile.insert(i+1, "@lw_usersettings {")
            caddyfile.insert(i+2, "  path /settings/users")
            caddyfile.insert(i+3, "  path /index.php/settings/users")
            caddyfile.insert(i+4, "}")
            caddyfile.insert(i+5, "handle @lw_usersettings {")
            caddyfile.insert(i+6, f"  redir https://portal.{domain}" + reverse("user_overview"))
            caddyfile.insert(i+7, "}")
            break

    with open("/etc/caddy/Caddyfile", "w") as f:
        f.write("\n".join(caddyfile))
    os.system("systemctl restart caddy")


def enable_nextcloud_user_administration():
    if is_nextcloud_user_administration_enabled():
        return
    # Open caddyfile lines and remove the lines "handle_path /index.php/settings/users" and "redir https://portal.{domain}/" + reverse("user_overview")
    caddyfile = open("/etc/caddy/Caddyfile").read()
    caddyfile = caddyfile.split("\n")
    for i, line in enumerate(caddyfile):
        if "@lw_usersettings {" in line:
            for j in range(7):
                del caddyfile[i]
            break

    with open("/etc/caddy/Caddyfile", "w") as f:
        f.write("\n".join(caddyfile))
    os.system("systemctl restart caddy")


def get_additional_services_control_files():
    """Returns a tuple with the content of (1) start_additional_services.sh and (2) stop_additional_services.sh"""
    start_additional_services = ""
    stop_additional_services = ""
    if os.path.isfile("/var/lib/libre-workspace/portal/start_additional_services.sh"):
        start_additional_services = open("/var/lib/libre-workspace/portal/start_additional_services.sh").read()
    if os.path.isfile("/var/lib/libre-workspace/portal/stop_additional_services.sh"):
        stop_additional_services = open("/var/lib/libre-workspace/portal/stop_additional_services.sh").read()
    return (start_additional_services, stop_additional_services)


def set_additional_services_control_files(start_additional_services, stop_additional_services):
    """Sets the content of (1) start_additional_services.sh and (2) stop_additional_services.sh"""
    with open("/var/lib/libre-workspace/portal/start_additional_services.sh", "w") as f:
        f.write(start_additional_services)
    with open("/var/lib/libre-workspace/portal/stop_additional_services.sh", "w") as f:
        f.write(stop_additional_services)


def is_systemd_service_running(service):
    return os.system(f"systemctl is-active --quiet {service}") == 0


def is_unix_service_running():
    """Checks if libre-workspace-service.service is running"""
    return is_systemd_service_running("libre-workspace-service")


def is_samba_ad_dc_running():
    return is_systemd_service_running("samba-ad-dc")


def update_libre_workspace():
    """Updates the Libre Workspace to the latest version"""
    # If /usr/lib/libre-workspace/portal/update_libre_workspace.sh exists
    if not os.path.isfile("/usr/lib/libre-workspace/portal/update_libre_workspace.sh"):
        return "Error: update_libre_workspace.sh not found."
    subprocess.Popen(["/usr/bin/bash", "/usr/lib/libre-workspace/portal/update_libre_workspace.sh"], cwd="/usr/lib/libre-workspace/portal/")


# Cache the version of the new Libre Workspace version for 1 hour
cached_libre_workspace_update_available = None
cached_libre_workspace_update_available_time = None
def is_libre_workspace_update_available():
    """Returns null or the version of the new Libre Workspace version"""

    global cached_libre_workspace_update_available
    global cached_libre_workspace_update_available_time

    if cached_libre_workspace_update_available_time and cached_libre_workspace_update_available_time + 3600 > time.time():
        return cached_libre_workspace_update_available

    # Get github releases
    response = requests.get("https://api.github.com/repos/jean28518/libre-workspace/releases")

    # If we can't reach the github api, return None
    if response.status_code != 200:
        cached_libre_workspace_update_available = None
        cached_libre_workspace_update_available_time = time.time()
        return None
    
    releases = response.json()
    # Get the latest release
    print(releases)
    latest_release = releases[0]
    # Get the version string
    latest_version = latest_release["tag_name"]
    # Remove the v from the version string
    if latest_version[0] == "v":
        latest_version = latest_version[1:]
    # Get the current version
    current_version = get_libre_workspace_version()
    # Compare the versions
    if latest_version != current_version:
        cached_libre_workspace_update_available = latest_version
    else:
        cached_libre_workspace_update_available = None
    cached_libre_workspace_update_available_time = time.time()
    return cached_libre_workspace_update_available


# We implement no automatic delete function for the groupfolders,
# because in them could be important data of the users.
# The admin has to remove the groupfolders manually in the nextcloud web interface.
def create_nextcloud_groupfolder(group):
    # If we are not running as root, return
    if os.getuid() != 0:
        return "Error: You should run this function as root. In development mode this is okay for now."
    # If nextcloud is not available, return
    if not is_nextcloud_installed():
        return "Error: Nextcloud is not available. Please install Nextcloud first."

    # Example for groupname test:
    # sudo -u www-data php /var/www/nextcloud/occ groupfolder:create test -> returns 1 as groupfolder_id
    # sudo -u www-data php /var/www/nextcloud/occ groupfolder:group 1 test read
    # sudo -u www-data php /var/www/nextcloud/occ groupfolders:group 1 test write
    # sudo -u www-data php /var/www/nextcloud/occ groupfolders:group 1 test create
    # sudo -u www-data php /var/www/nextcloud/occ groupfolders:group 1 test share
    # sudo -u www-data php /var/www/nextcloud/occ groupfolders:group 1 test delte
    groupfolder_id = subprocess.getoutput(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolder:create {group}").strip()
    # if groupfolder_id is not numeric, then the groupfolder was not created
    if not groupfolder_id.isnumeric():
        return groupfolder_id # Then return the error message
    
    # At first make sure that the new group is already synced from the LDAP server (ldap:check-group)
    os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ ldap:check-group {group}")

    os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolder:group {groupfolder_id} {group} read")
    os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolders:group {groupfolder_id} {group} write")
    os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolders:group {groupfolder_id} {group} create")
    os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolders:group {groupfolder_id} {group} share")
    os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolders:group {groupfolder_id} {group} delete")


def nextcloud_groupfolder_exists(group):
    # Check if the groupfolder exists
    if not is_nextcloud_installed():
        return False
    # If we are not running as root, return
    if os.getuid() != 0:
        return False
    return os.system(f"sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ groupfolder:list | grep -q {group}") == 0


def is_xfce_installed():
    return os.path.isdir("/usr/share/xfce4")

def is_samba_dc_installed():
    return os.path.isdir("/root/samba_dc")


def change_password_for_linux_user(username, new_password):
    """Only changes the password for the user in the linux operating system, if the user exists. Otherwise, it does nothing."""
    # Check if the user exists
    if os.system(f"getent passwd {username}") != 0:
        return
    # If user is not member of the libre-workspace-users group, return
    if os.system(f"groups {username} | grep -q libre-workspace-users") != 0:
        return
    # Change the password for the user in the linux operating system
    return_code = os.system(f"echo \"{username}:{new_password}\" | chpasswd")
    if return_code != 0:
        return "Error: Password for user in linux: could not be changed."
    return


def get_system_data_for_support():
    """Creates a zip file with all necessary data for the support."""

    # Create a temporary directory
    os.system("rm -r /tmp/support_data/")
    os.system("mkdir /tmp/support_data/")

    # Copy the files to the temporary directory
    files_to_copy = ["/etc/caddy/Caddyfile", "/etc/hosts", "/etc/resolv.conf", "/etc/samba/smb.conf", "/etc/krb5.conf", "/etc/ssh/sshd_config", "/etc/fstab", "/etc/libre-workspace/portal/portal.conf", "/var/log/syslog", "/etc/libre-workspace/libre-workspace.env", "/etc/libre-workspace/libre-workspace.conf", "/etc/os-release"]
    for file in files_to_copy:
        os.system(f"cp {file} /tmp/support_data/")
        # For every line which contains the word password or passphrase, replace the line with "PASSWORD REMOVED"
        try:
            lines = open(f"/tmp/support_data/{file.split('/')[-1]}").readlines()
        except:
            continue
        for i, line in enumerate(lines):
            if "password" in line.lower() or "passphrase" in line.lower() or "secret" in line.lower():
                lines[i] = "*** PASSWORD/SECRET REMOVED ***\n"
        with open(f"/tmp/support_data/{file.split('/')[-1]}", "w") as f:
            f.write("".join(lines))
            f.close()

    # Get the output of df -h and ip a
    commands = ["df -h", "ip a"]
    for command in commands:
        output = subprocess.getoutput(command)
        with open(f"/tmp/support_data/{command.replace(' ', '_')}", "w") as f:
            f.write(output)
            f.close()

    # Create the zip file
    os.system("cd /tmp/; zip -r support_data.zip support_data/")

    # Mv the zip file to static folder
    os.system("mv /tmp/support_data.zip /var/www/libre-workspace-static/support_data.zip")

    # Start a process which deletes the temporary directory and .zip file after 5 minutes
    subprocess.Popen(["/usr/bin/bash", "-c", "sleep 300; rm -r /tmp/support_data/"])
    subprocess.Popen(["/usr/bin/bash", "-c", "sleep 300; rm /var/www/libre-workspace-static/support_data.zip"])


def get_local_admin_token():
    """Returns the local admin token"""
    local_token_file_content = os.popen("cat /var/lib/libre-workspace/local-admin-token").read()
    local_token_file_content = local_token_file_content.replace("LW_ADMIN_TOKEN=", "")
    if local_token_file_content.strip() == "":
        print("CAUTION: No local admin token found. If you are in a dev environment, this is okay. If you are in a production environment, please check your installation, your system is not secure.")
        return None
    return local_token_file_content.strip()


def generate_local_admin_token():
    """Generates a new local admin token. This admin token is only valid to the next restart of libre workspace web."""
    # Generate a random token
    token = os.popen("openssl rand -hex 4096").read().strip()
    # Save the token to /var/lib/libre-workspace/local-admin-token
    os.system(f"echo \"LW_ADMIN_TOKEN={token}\" > /var/lib/libre-workspace/local-admin-token")
    # Set the permissions for the file
    os.system("chmod 600 /var/lib/libre-workspace/local-admin-token")
    os.system("chown root:root /var/lib/libre-workspace/local-admin-token")
