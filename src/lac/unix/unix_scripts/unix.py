import os
import time
import subprocess

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
    if os.path.isfile("disabled"):
        rv["backup_status"] = "deactivated"

    # If the repository is not configured, set backup status to "not_configured"
    if get_value("BORG_REPOSITORY") == "":
        rv["backup_status"] = "not_configured"

    # If everything is okay but no backup has been made yet, set backup status to "no_backup_yet"
    if rv["backup_status"] == "ok" and len(rv["backup_history"]) == 0:
        rv["backup_status"] = "no_backup_yet"

    return rv

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
    if os.path.isfile("disabled"):
        return
    # If the repository is not configured, exit
    if config["BORG_REPOSITORY"] == "":
        return
    print("TOUCHING")
    # Remove the history file of today
    date = time.strftime("%Y-%m-%d")
    print(date)
    if os.path.isfile(f"history/borg_errors_{date}.log"):
        os.remove(f"history/borg_errors_{date}.log")
    os.system("touch run_service")

def is_backup_enabled():
    # Return True if backup is enabled, False if backup is disabled
    return not os.path.isfile("disabled")

def set_backup_enabled(enabled):
    # Enable or disable the backup
    if enabled:
        if os.path.isfile("disabled"):
            os.remove("disabled")
    else:
        if not os.path.isfile("disabled"):
            os.system("touch disabled")


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
        if "/dev/loop" in name or "udev" in name or "tmpfs" in name:
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
    rv["total_ram"] = subprocess.getoutput("free -h").split("\n")[1].split()[1].replace("Gi", "")
    rv["ram_usage"] = subprocess.getoutput("free -h").split("\n")[1].split()[2].replace("Gi", "")
    rv["uptime"] = subprocess.getoutput("uptime -p").replace("up", "").replace("minutes", "Minuten").replace("hours", "Stunden").replace("days", "Tage").replace("weeks", "Wochen").replace("years", "Jahre")
    rv["os"] = subprocess.getoutput("cat /etc/os-release").split("\n")[0].split("=")[1].strip('"')
    return rv