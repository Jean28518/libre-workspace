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

# Change current directory to the directory of this script
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# If the config file does not exist, create it
if not os.path.isfile("unix.conf"):
    os.system("touch unix.conf")  
    

config = {}

def read_config_file():
    # Read the config file
    for line in open("unix.conf"):
        if line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        # remove the " and ' characters from the outer ends of the string
        config[key.strip()] = value.strip("'\"\n ")

def write_config_file():
    # Write the config file
    with open("unix.conf", "w") as f:
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
    if os.path.isfile("history/borg_info"):
        lines = open("history/borg_info").readlines()
        for line in lines:
            if line.startswith("All archives:"):
                size = line[-15:-1].strip()
                rv["compressed_size_of_all_backups"] = size
    
    rv["encrypted"] = get_value("BORG_ENCRYPTION") == "true"

    rv["backup_status"] = "ok"

    # Get all archives
    rv["archives"] = []
    if os.path.isfile("history/borg_list"):
        lines = open("history/borg_list").readlines()
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
    for file in os.listdir("history"):
        if file.startswith("borg_errors_"):
            entry = {}
            # Get the date from the filename
            date = file[12:-4]
            # Get the error message from the file
            error = open(f"history/{file}").read()
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
    
    # If file "backup_running" exists, set backup status to "running"
    if os.path.isfile("maintenance/backup_running"):
        rv["backup_status"] = "running"
    
    if os.path.isfile("maintenance/recovery_running"):
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
    if os.path.isfile("id_rsa.pub"):
        return open("id_rsa.pub").read()
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
    if os.path.isfile("maintenance/backup_running"):
        return
    # If the backup is deactivated, exit
    if os.path.isfile("maintenance/backup_disabled"):
        return
    # If the repository is not configured, exit
    if config["BORG_REPOSITORY"] == "":
        return
    # Remove the history file of today
    date = time.strftime("%Y-%m-%d")
    if os.path.isfile(f"history/borg_errors_{date}.log"):
        os.remove(f"history/borg_errors_{date}.log")
    trigger_cron_service()

def is_backup_enabled():
    # Return True if backup is enabled, False if backup is disabled
    return not os.path.isfile("maintenance/backup_disabled")

def set_backup_enabled(enabled):
    # Enable or disable the backup
    if enabled:
        if os.path.isfile("maintenance/backup_disabled"):
            os.remove("maintenance/backup_disabled")
    else:
        if not os.path.isfile("maintenance/backup_disabled"):
            os.system("touch maintenance/backup_disabled")


def get_disks_stats():
    # Return disk name, the mountpoint, the foll size and the used size.
    lines = subprocess.getoutput("df -h")

    lines = lines.split("\n")
    lines = lines[1:]
    disks = []
    for line in lines:
        line = line.split(" ")
        while '' in line:
            line.remove('')
        name = line[0]
        if "/dev/loop" in name or "udev" in name or "tmpfs" in name or "overlay" in name:
            continue
        size = line[1]
        # If the size is in megabytes, skip this disk, because it is very small
        if "M" in size:
            continue
        disk = {}
        disk["name"] = name.replace("/dev/", "")
        disk["size"] = size
        disk["used"] = line[2]
        disk["used_percent"] = line[4].replace("%", "")
        disk["mountpoint"] = line[5]
        disks.append(disk)
    return disks


def get_system_information():
    # Get hostname, ram usage, cpu usage, uptime, os version
    rv = {}
    rv["lw_name"] = get_libre_workspace_name()
    rv["lw_version"] = get_libre_workspace_version()
    rv["hostname"] = subprocess.getoutput("hostname")

    rv["total_ram"] = subprocess.getoutput("free -h").split("\n")[1].split()[1].replace("Gi", "").replace("Mi", "")
    ram_usage = subprocess.getoutput("free -h").split("\n")[1].split()[2]
    if "Mi" in ram_usage:
        rv["ram_usage"] = str(int(ram_usage.replace("Mi", ""))/1024).replace(".", ",")
    else:
        rv["ram_usage"] = ram_usage.replace("Gi", "")
    rv["ram_percent"] = int(float(rv["ram_usage"].replace(",", ".")) / float(rv["total_ram"].replace(",", ".")) * 100)

    load_avg = subprocess.getoutput("cat /proc/loadavg").split(" ")[0]
    cpu_number = subprocess.getoutput("nproc")
    rv["cpu_usage_percent"] = int(float(load_avg) / float(cpu_number) * 100)

    rv["uptime"] = subprocess.getoutput("uptime -p").replace("up", "").replace("minutes", "Minuten").replace("hours", "Stunden").replace("days", "Tage").replace("weeks", "Wochen").replace("months", "Monate").replace("years", "Jahre")
    rv["uptime"] = rv["uptime"].replace("min", "Min").replace("hour", "Stunde").replace("day", "Tag").replace("week", "Woche").replace("month", "Monat").replace("year", "Jahr")
    rv["os"] = subprocess.getoutput("cat /etc/os-release").split("\n")[0].split("=")[1].strip('"')


    rv["update_information"] = f"{get_upgradable_packages()} Pakete können aktualisiert werden." if get_upgradable_packages() > 0 else "Das System ist auf dem neuesten Stand."
    if os.path.exists("history/update.log") and not is_update_currently_running():
        rv["last_update_log"] = open("history/update.log").read().replace("\n", " <br> ")
    if is_update_currently_running():
        rv["update_information"] = "Das System wird gerade aktualisiert..."
    return rv


def get_upgradable_packages():
    if not os.path.isfile("maintenance/upgradable_packages"):
        return 0
    return int(subprocess.getoutput("cat maintenance/upgradable_packages | wc -l")) -1


def is_update_currently_running():
    return os.path.isfile("maintenance/update_running")


def trigger_cron_service():
    # If the run_service file exists, remove it and run service immediately
    os.system("touch run_service")

def update_system():
    # If the update is currently running, exit
    if os.path.isfile("maintenance/update_system"):
        return
    os.system("touch maintenance/update_system")
    trigger_cron_service()
    


def reboot_system():
    os.system("/sbin/shutdown -r now")


def shutdown_system():
    os.system("/sbin/shutdown -h now")


def start_all_services():
    subprocess.Popen(["/usr/bin/bash", "start_services.sh"], cwd="maintenance/", env=get_env_from_unix_conf())


def stop_all_services():
    subprocess.Popen(["/usr/bin/bash", "stop_services.sh"], cwd="maintenance/", env=get_env_from_unix_conf())


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
    if not os.path.isfile("history/rsync.log"):
        return ""
    rsync_history = open("history/rsync.log").read().replace("\n", "<br>")
    return rsync_history

def is_nextcloud_available():
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
            if ldap_user["objectGUID"].upper()[-8:-1] == nextcloud_user["name"].replace("-", "")[-8:-1]:
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

def is_matrix_available():
    return os.path.isdir("/root/matrix/")


def is_jitsi_available():
    return os.path.isdir("/root/jitsi/")


def is_collabora_available():
    return os.path.isdir("/root/collabora/")


def is_onlyoffice_available():
    return os.path.isdir("/root/onlyoffice/")


def get_software_modules():
    modules = []
    if is_nextcloud_available():
        modules.append({ "id": "nextcloud", "name": "Nextcloud", "automaticUpdates": get_value("NEXTCLOUD_AUTOMATIC_UPDATES", "False") == "True", "installed": True })
    else:
        modules.append({ "id": "nextcloud", "name": "Nextcloud", "automaticUpdates": get_value("NEXTCLOUD_AUTOMATIC_UPDATES", "False") == "True", "installed": False })
    if is_matrix_available():
        modules.append({ "id": "matrix", "name": "Matrix", "automaticUpdates": get_value("MATRIX_AUTOMATIC_UPDATES", "False") == "True", "installed": True })
    else:
        modules.append({ "id": "matrix", "name": "Matrix", "automaticUpdates": get_value("MATRIX_AUTOMATIC_UPDATES", "False") == "True", "installed": False })
    if is_jitsi_available():
        modules.append({ "id": "jitsi", "name": "Jitsi", "automaticUpdates": get_value("JITSI_AUTOMATIC_UPDATES", "False") == "True", "installed": True })
    else:
        modules.append({ "id": "jitsi", "name": "Jitsi", "automaticUpdates": get_value("JITSI_AUTOMATIC_UPDATES", "False") == "True", "installed": False })
    if is_collabora_available():
        modules.append({ "id": "collabora", "name": "Collabora", "automaticUpdates": get_value("COLLABORA_AUTOMATIC_UPDATES", "False") == "True", "installed": True })
    else:
        modules.append({ "id": "collabora", "name": "Collabora", "automaticUpdates": get_value("COLLABORA_AUTOMATIC_UPDATES", "False") == "True", "installed": False })
    if is_onlyoffice_available():
        modules.append({ "id": "onlyoffice", "name": "OnlyOffice", "automaticUpdates": get_value("ONLYOFFICE_AUTOMATIC_UPDATES", "False") == "True", "installed": True })
    else:
        modules.append({ "id": "onlyoffice", "name": "OnlyOffice", "automaticUpdates": get_value("ONLYOFFICE_AUTOMATIC_UPDATES", "False") == "True", "installed": False })
    
    for module in modules:
        module["scriptsFolder"] = f"{module['id']}"

    # Get addons:
    addons = get_all_addon_modules()
    for addon in addons:
        addon["installed"] = is_module_installed(addon["id"])
        addon["automaticUpdates"] = get_value(f"{addon['id'].upper().replace('-', '_')}_AUTOMATIC_UPDATES", "False") == "True"
        addon["scriptsFolder"] = f"addons/{addon['id']}"
        modules.append(addon)


    return modules


# We determine if a module is installed by checking if the module's directory exists in the root directory
def is_module_installed(module_or_addon: str):
    """ 
    If this is True, then the module or addon is really installed into the server.
    """
    return os.path.isdir(f"/root/{module_or_addon}")


def get_update_history():
    history = []
    for file in os.listdir("history"):
        if file.startswith("update-"):
            entry = {}
            entry["date"] = file[7:-4]
            entry["content"] = open(f"history/{file}").read().replace("\n", "<br>")
            history.append(entry)
    history = sorted(history, key=lambda k: k['date'], reverse=True)
    return history


def get_update_information():
    update_information = {}
    update_information["software_modules"] = get_software_modules()
    update_information["software_modules"].insert(0, {"id": "system", "name": "System", "installed": True, "automaticUpdates": get_value("SYSTEM_AUTOMATIC_UPDATES", "False") == "True"})
    update_information["software_modules"].insert(0, {"id": "libre_workspace", "name": "Libre Workspace (venv)", "installed": True, "automaticUpdates": get_value("LIBRE_WORKSPACE_AUTOMATIC_UPDATES", "False") == "True"})
    update_information["update_time"] = get_value("UPDATE_TIME", "02:00")
    update_information["update_history"] = get_update_history()
    print(update_information)
    return update_information

def get_env_sh_variables():
    return_value = {}
    if not os.path.isfile("env.sh"):
        return return_value
    for line in open("env.sh").readlines():
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
    if os.path.isdir(f"addons/{module_name}"):
        return f"addons/{module_name}"
    return module_name


# Also "installs" addons
def setup_module(module_name):
    module_path = get_module_path(module_name)
    # Check if module is an addon:
    if "addon" in module_path:
        # Add the entry to the /etc/hosts file
        addon = get_config_of_addon(module_name)
        url = addon.get("url", "")
        if url == "":
            return f"No URL found in the config file of the addon {module_name}. Please check the config file of the addon."
        
        # Lets generate the samba_domain from LDAP_DC in env.sh
        samba_domain = get_env_sh_variables().get("LDAP_DC", "")
        if samba_domain == "":
            return "No LDAP_DC found in the env.sh file. Please check the env.sh file."
        
        # Remove the dc= and ,dc= from the domain
        samba_domain = samba_domain.replace("dc=", "").replace(",", ".")

        ip = get_env_sh_variables().get("IP", "")   
        os.system(f"echo \"{ip} {url}.{samba_domain}\" >> /etc/hosts")

        # Add the entry to the DNS server
        if settings.AUTH_LDAP_ENABLED:
            admin_password = get_env_sh_variables().get("ADMIN_PASSWORD", "")
            # Run this command: samba-tool dns add la.$DOMAIN $DOMAIN matrix A $IP -U administrator%$ADMIN_PASSWORD
            os.system(f"samba-tool dns add la.{samba_domain} {samba_domain} {url} A {ip} -U administrator%{admin_password}")
        

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
        url = addon.get("url", "")
        if url == "":
            return f"No URL found in the config file of the addon {module_name}. Please check the config file of the addon."
        domain = get_env_sh_variables().get("DOMAIN", "")
        if domain == "":
            return "No domain found in the env.sh file. Please check the env.sh file."
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
    if is_collabora_available():
        return "collabora"
    if is_onlyoffice_available():
        return "onlyoffice"
    return None


def mount_backups():
    process = subprocess.Popen(["/usr/bin/bash", "mount_backups.sh"], cwd="maintenance/", env=get_env_from_unix_conf())
    time.sleep(5)
    if process.returncode != None and process.returncode != 0:
        return "Error: Mounting backups failed: " + str(process.stdout) + " " + str(process.stderr)


def umount_backups():
    process = subprocess.Popen(["/usr/bin/bash", "umount_backups.sh"], cwd="maintenance/", env=get_env_from_unix_conf())
    time.sleep(1)
    if process.returncode != None and process.returncode != 0:
        return "Error: Umounting backups failed: " + str(process.stdout) + " " + str(process.stderr)
    

# This function needs the location in the backup to recover and the location to recover to
# Example: full_path_to_backup = "/backup/2021-01-01_12-00-00", full_path_to_recover_to = "/mnt/restore"
def recover_file_or_dir(full_path_to_backup):
    process = subprocess.Popen(["/usr/bin/bash", "recover_path.sh", full_path_to_backup], cwd="maintenance/", env=get_env_from_unix_conf(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    if process.returncode != None and process.returncode != 0:
        return "Error: Recovering file or directory failed: " + str(process.stdout.read()) + " " + str(process.stderr.read())
    

def is_path_a_file(path):
    return os.path.isfile(path)


# Returns array with all configs
def get_all_addon_modules():
    # Get all folders in the addons directory
    addons = []
    for folder in os.listdir("addons"):
        if os.path.isdir(f"addons/{folder}"):
            addons.append(get_config_of_addon(folder))
    return addons


def get_config_of_addon(addon):
    # Read the config file of the addon
    config = {}
    for line in open(f"addons/{addon}/{addon}.conf"):
        if line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        # remove the " and ' characters from the outer ends of the string
        config[key.strip()] = value.strip("'\"\n ")
        # Get icon file format
        for file in os.listdir(f"addons/{addon}"):
            if file.endswith(".png") or file.endswith(".svg") or file.endswith(".jpg") or file.endswith(".webp"):
                config["icon_file_format"] = file.split(".")[-1]
    return config


def install_addon(path_to_zip_file):
    addon_id = path_to_zip_file.split('/')[-1].split('.')[0]
    # Remove the old folder of the addon if it exists
    os.system(f"rm -r addons/{addon_id}")
    os.system(f"unzip {path_to_zip_file} -d addons/")
    os.system(f"rm {path_to_zip_file}")
    # Copy the image file which could have the ending .png .svg .jpg .webp to the static folder
    for file in os.listdir(f"addons/{addon_id}"):
        if file.endswith(".png") or file.endswith(".svg") or file.endswith(".jpg") or file.endswith(".webp"):
            os.system(f"cp addons/{addon_id}/{file} ../../lac/static/lac/icons/{file}")
            # Also copy to /var/www/linux-arbeitsplatz-static/lac/icons/ (that is the folder where the static files are served from)
            os.system(f"cp addons/{addon_id}/{file} /var/www/linux-arbeitsplatz-static/lac/icons/{file}")
            os.system(f"chown www-data:www-data /var/www/linux-arbeitsplatz-static/lac/icons/{file}")
            os.system(f"chmod 644 /var/www/linux-arbeitsplatz-static/lac/icons/{file}")


def uninstall_addon(addon_id):
    """"
    Removes the folder of the addon. Don't uninstall the addon if it is currently installed into the server.
    """
    addon_information = get_config_of_addon(addon_id)
    os.system(f"rm -r addons/{addon_id}")
    os.system(f"rm ../../lac/static/lac/icons/{addon_id}.*")
    os.system(f"rm /var/www/linux-arbeitsplatz-static/lac/icons/{addon_id}.*")
    # Remove the entry from the AppDashboardEntry table in the database
    DashboardEntry.objects.filter(title=addon_information["name"], is_system=True).delete()


def get_all_installed_nextcloud_addons():
    """"
    Returns a list of all installed nextcloud addons.
    """
    addons = []
    if not is_nextcloud_available():
        return addons
    for folder in os.listdir(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/apps"):
        if os.path.isdir(settings.NEXTCLOUD_INSTALLATION_DIRECTORY + "/apps/" + folder):
            addons.append(folder)
    return addons


def restart_linux_arbeitsplatz_web():
    # Only run this command one second after the function was called to ensure that the response is sent to the client before the server restarts
    subprocess.Popen("sleep 1; systemctl restart linux-arbeitsplatz-web",shell=True)


def get_libre_workspace_name():
    domain = get_env_sh_variables().get("DOMAIN", "")
    return get_value(f"LIBRE_WORKSPACE_NAME", f"{domain} - Libre Workspace")


def set_libre_workspace_name(name):
    set_value("LIBRE_WORKSPACE_NAME", name)


def get_libre_workspace_version():
    # Get the version of installed linux-arbeitsplatz.deb:
    output = subprocess.getoutput("dpkg -s linux-arbeitsplatz | grep Version")
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
    os.system("pam-auth-update --disable krb5")
    os.system(f"chpasswd <<<\"systemv:{password}\"")
    os.system("pam-auth-update --enable krb5")

    # Update the password in the env.sh file
    os.system(f"sed -i 's/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=\"{password}\"/g' env.sh")

    # Change the configured bind password in /usr/share/linux-arbeitsplatz/cfg
    os.system(f"sed -i 's/AUTH_LDAP_BIND_PASSWORD=.*/AUTH_LDAP_BIND_PASSWORD=\"{password}\"/g' /usr/share/linux-arbeitsplatz/cfg")

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

    # Change the IP in the env.sh file
    os.system(f"sed -i 's/IP=.*/IP=\"{ip}\"/g' env.sh")

    # Change the IP in the /etc/hosts file
    os.system(f"sed -i 's/{old_ip}/{ip}/g' /etc/hosts")

    # Change the IP in the DNS server of samba
    domain = get_env_sh_variables().get("DOMAIN", "")
    admin_password = get_env_sh_variables().get("ADMIN_PASSWORD", "")

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

    # Change all old ips with the new ip in /usr/share/linux-arbeitsplatz/welcome/templates/welcome/access_rendered.html
    os.system(f"sed -i 's/{old_ip}/{ip}/g' /usr/share/linux-arbeitsplatz/welcome/templates/welcome/access_rendered.html")

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
    # Check if   handle_path /index.php/settings/users is in the Cadddyfile
    caddyfile = open("/etc/caddy/Caddyfile").read()
    return not ("handle_path /index.php/settings/users" in caddyfile)


def enable_nextcloud_user_administration():
    if is_nextcloud_user_administration_enabled():
        return
    domain = get_env_sh_variables().get("DOMAIN", "")
    # Open caddyfile lines and add the line "handle_path /index.php/settings/users" after the line where cloud. is in
    caddyfile = open("/etc/caddy/Caddyfile").read()
    caddyfile = caddyfile.split("\n")
    for i, line in enumerate(caddyfile):
        if "cloud." in line:
            caddyfile.insert(i+1, "handle_path /index.php/settings/users {")
            caddyfile.insert(i+2, f"  redir https://portal.{domain}/" + reverse("user_overview"))
            caddyfile.insert(i+3, "}")
            break

    with open("/etc/caddy/Caddyfile", "w") as f:
        f.write("\n".join(caddyfile))
    os.system("systemctl reload caddy")


def disable_nextcloud_user_administration():
    if not is_nextcloud_user_administration_enabled():
        return
    # Open caddyfile lines and remove the lines "handle_path /index.php/settings/users" and "redir https://portal.{domain}/" + reverse("user_overview")
    caddyfile = open("/etc/caddy/Caddyfile").read()
    caddyfile = caddyfile.split("\n")
    for i, line in enumerate(caddyfile):
        if "handle_path /index.php/settings/users" in line:
            del caddyfile[i]
            del caddyfile[i]
            del caddyfile[i]
            break

    with open("/etc/caddy/Caddyfile", "w") as f:
        f.write("\n".join(caddyfile))
    os.system("systemctl reload caddy")
    