import os
import time
import subprocess
import json
import lac.settings as settings
import idm.ldap as ldap

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

def get_value(key):
    read_config_file()
    # Get the value of a key from the config file
    if key in config:
        return config[key]
    else:
        return ""
    
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
    if os.path.isfile("backup_running"):
        rv["backup_status"] = "running"

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
    if os.path.isfile("backup_running"):
        return
    # If the backup is deactivated, exit
    if os.path.isfile("backup_disabled"):
        return
    # If the repository is not configured, exit
    if config["BORG_REPOSITORY"] == "":
        return
    # Remove the history file of today
    date = time.strftime("%Y-%m-%d")
    print(date)
    if os.path.isfile(f"history/borg_errors_{date}.log"):
        os.remove(f"history/borg_errors_{date}.log")
    trigger_cron_service()

def is_backup_enabled():
    # Return True if backup is enabled, False if backup is disabled
    return not os.path.isfile("backup_disabled")

def set_backup_enabled(enabled):
    # Enable or disable the backup
    if enabled:
        if os.path.isfile("backup_disabled"):
            os.remove("backup_disabled")
    else:
        if not os.path.isfile("backup_disabled"):
            os.system("touch backup_disabled")


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
    rv["hostname"] = subprocess.getoutput("hostname")
    rv["total_ram"] = subprocess.getoutput("free -h").split("\n")[1].split()[1].replace("Gi", "").replace("Mi", "")
    rv["ram_usage"] = subprocess.getoutput("free -h").split("\n")[1].split()[2].replace("Gi", "").replace("Mi", "")
    rv["ram_percent"] = int(float(rv["ram_usage"].replace(",", ".")) / float(rv["total_ram"].replace(",", ".")) * 100)
    rv["uptime"] = subprocess.getoutput("uptime -p").replace("up", "").replace("minutes", "Minuten").replace("hours", "Stunden").replace("days", "Tage").replace("weeks", "Wochen").replace("years", "Jahre")
    rv["os"] = subprocess.getoutput("cat /etc/os-release").split("\n")[0].split("=")[1].strip('"')


    rv["update_information"] = f"{get_upgradable_packages()} Pakete können aktualisiert werden." if get_upgradable_packages() > 0 else "Das System ist auf dem neuesten Stand."
    if os.path.exists("history/update.log") and not is_update_currently_running():
        rv["last_update_log"] = open("history/update.log").read().replace("\n", " <br> ")
    if is_update_currently_running():
        rv["update_information"] = "Das System wird gerade aktualisiert..."
    return rv


def get_upgradable_packages():
    if not os.path.isfile("upgradable_packages"):
        return 0
    return int(subprocess.getoutput("cat upgradable_packages | wc -l")) -1


def is_update_currently_running():
    return os.path.isfile("update_running")


def trigger_cron_service():
    # If the run_service file exists, remove it and run service immediately
    os.system("touch run_service")

def update_system():
    # If the update is currently running, exit
    if os.path.isfile("update_system"):
        return
    os.system("touch update_system")
    trigger_cron_service()
    


def reboot_system():
    os.system("/sbin/shutdown -r now")


def shutdown_system():
    os.system("/sbin/shutdown -h now")


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
    return folders


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