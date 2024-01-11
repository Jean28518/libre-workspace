# Called from root crontab every minute
import os
import unix_config # (its in the same directory)
import time
from datetime import datetime

# If cron is not running as root, exit
if os.geteuid() != 0:
    print("Cron is not running as root. Exiting.")
    exit()

print("Running unix service...")

# Change current directory to the directory of this script
os.chdir(os.path.dirname(os.path.realpath(__file__)))

def ensure_fingerprint_is_trusted():
    ## Ensure trusted ssh fingerprints are available
    # Fingerprint is located in trusted_fingerprints file
    # If the fingerprints are not in the /root/.ssh/known_hosts file, add them
    if not os.path.isfile("/root/.ssh/known_hosts"):
        os.system("touch /root/.ssh/known_hosts")
    known_hosts = open("/root/.ssh/known_hosts").readlines()
    if os.path.isfile("trusted_fingerprints"):
        trusted_fingerprints = open("trusted_fingerprints").readlines()
        for fingerprint in trusted_fingerprints:
            if fingerprint not in known_hosts:
                known_hosts.append(fingerprint)
    # Write the fingerprints to the /root/.ssh/known_hosts file
    with open("/root/.ssh/known_hosts", "w") as f:
        f.writelines(known_hosts)

def ensure_rocketchat_settings():
    time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # Count the number of files with name "rocketchat" in history directory
    history_files = os.listdir("history")
    rocketchat_files = []
    for history_file in history_files:
        if "rocketchat" in history_file:
            rocketchat_files.append(history_file)
    # If there are more than 5 files with name "rocketchat" in history directory, exit
    if len(rocketchat_files) >= 5:
        return
    
    # Find the latest file with name "rocketchat" in history directory
    # Only run if the latest file was created more than 5 minutes ago
    if len(rocketchat_files) > 0:
        latest_file = rocketchat_files[0]
        for rocketchat_file in rocketchat_files:
            if rocketchat_file > latest_file:
                latest_file = rocketchat_file
        # If the latest file was created less than 5 minutes ago, exit
        latest_time = latest_file.split("_")[1].split(".")[0]
        # Get time of latest file
        latest_file = datetime.strptime(latest_time, "%Y-%m-%d-%H-%M-%S")
        if (datetime.now() - latest_file).seconds < 300:
            return
    old_working_dir = os.getcwd()
    os.chdir("../../welcome/scripts")
    print("Ensuring rocketchat settings...")
    os.system("python3 configure_rockechat_ldap.py")
    os.chdir(old_working_dir)
    os.system("touch history/rocketchat_" + time + ".set")



counter = 60
hourly_counter = 3600
while True:
    ## Run every minute ############################################################################################
    # If run_service file exists, remove it and run service immediately
    time.sleep(1)
    counter += 1
    hourly_counter += 1
    if os.path.isfile("run_service"):
        os.remove("run_service")
        counter = 60
        hourly_counter = 3600
    if counter < 60:
        continue
    counter = 0

    # Read config file
    unix_config.read_config_file()

    # Ensure rocketchat settings
    ensure_rocketchat_settings()

    ## BACKUP ######################################################################################################

    # Get backup time from config file
    if unix_config.get_value("BORG_REPOSITORY") != "" and not os.path.exists("backup_disabled"):
        ensure_fingerprint_is_trusted()
        backup_time = unix_config.get_value("BORG_BACKUP_TIME")
        date = time.strftime("%Y-%m-%d")

        # If current time is higher than backup time, run backup
        if time.strftime("%H:%M") > backup_time and not os.path.isfile("backup_running") and not os.path.isfile(f"history/borg_errors_{date}.log"):
            print("Running backup")
            os.system("bash ./do_backup.sh")

            # Send email to admin if backup failed
            read_errors = open(f"history/borg_errors_{date}.log").read()
            if read_errors.strip() != "":
                os.system("curl -X POST -F 'subject=💾❌ Backup mit Fehlern abgeschlossen❌' -F 'message=Das heutige Backup war nicht vollständig erfolgreich.\\nIm Anhang finden Sie die Fehlermeldungen' localhost:11123/unix/send_mail")

    ## SYSTEM UPDATE ################################################################################################

    # If a user manually requested an update, run update
    if os.path.isfile("update_system"):
        os.remove("update_system")
        print("Updating system")
        os.system("bash ./do_update.sh")

    # All other updates:
    update_time = unix_config.get_value("UPDATE_TIME")
    current_date = time.strftime("%Y-%m-%d")
    if time.strftime("%H:%M") > update_time and not os.path.isfile("update_running") and not os.path.isfile(f"history/update-{current_date}.log"):
        print("Starting automatic updates")
        os.system("bash ./update_everything.sh")


    ## DO DATA EXPORT ################################################################################################

    if os.path.isfile("data_export"):
        print("Exporting data")
        os.system("bash ./do_data_export.sh")

    ##################################################################################################################
    ## RUN EVERY HOUR ################################################################################################
    ##################################################################################################################

    if hourly_counter < 3600:
        continue
    hourly_counter = 0

    ## Get list of upgradable packages
    os.system("apt list --upgradable > upgradable_packages")


    ## Ensure public key of root user is available 
    # If public key of root user is not available, create it
    if not os.path.isfile("/root/.ssh/id_rsa.pub"):
        os.system("ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ''")
    os.system("cp /root/.ssh/id_rsa.pub .")
    os.system("chmod 444 id_rsa.pub")
    