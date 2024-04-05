# Called from root crontab every minute
import os
import unix_config # (its in the same directory)
import time
from datetime import datetime
import subprocess

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

    ## BACKUP ######################################################################################################

    # Get backup time from config file
    if unix_config.get_value("BORG_REPOSITORY") != "" and not os.path.exists("maintenance/backup_disabled"):
        ensure_fingerprint_is_trusted()
        backup_time = unix_config.get_value("BORG_BACKUP_TIME")
        date = time.strftime("%Y-%m-%d")

        # If current time is higher than backup time, run backup
        if time.strftime("%H:%M") > backup_time and not os.path.isfile("maintenance/backup_running") and not os.path.isfile(f"history/borg_errors_{date}.log"):
            print("Running backup")
            # Run do_backup.sh script with cwd in the maintenance directory
            p = subprocess.Popen(["bash", "do_backup.sh"], cwd="maintenance")
            p.wait()


            # Send email to admin if backup failed
            read_errors = open(f"history/borg_errors_{date}.log").read()
            if read_errors.strip() != "":
                # Full path of the log file:
                log_file = os.path.abspath(f"history/borg_errors_{date}.log")
                os.system(f"curl -X POST -F 'subject=💾❌ Backup mit Fehlern abgeschlossen❌' -F 'message=Das heutige Backup war nicht vollständig erfolgreich.\nIm Anhang finden Sie die Fehlermeldungen.' -F 'attachment_path={log_file}' localhost:11123/unix/send_mail")

    ## SYSTEM UPDATE ################################################################################################

    # If a user manually requested an update, run update
    if os.path.isfile("maintenance/update_system"):
        os.remove("maintenance/update_system")
        print("Updating system")
        p = subprocess.Popen(["bash", "do_update.sh"], cwd="maintenance")

    # All other updates:
    update_time = unix_config.get_value("UPDATE_TIME")
    current_date = time.strftime("%Y-%m-%d")
    if time.strftime("%H:%M") > update_time and not os.path.isfile("maintenance/update_running") and not os.path.isfile(f"history/update-{current_date}.log"):
        print("Starting automatic updates")
        p = subprocess.Popen(["bash", "update_everything.sh"], cwd="maintenance")
        p.wait()


    ## DO DATA EXPORT ################################################################################################

    if os.path.isfile("export_data"):
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
    