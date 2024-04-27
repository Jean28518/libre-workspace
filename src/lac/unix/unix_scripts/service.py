# Called from root crontab every minute
import os
import unix_config # (its in the same directory)
import time
from datetime import datetime
import subprocess
import utils

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
five_minute_counter = 300
while True:
    ## Run every minute ############################################################################################
    # If run_service file exists, remove it and run service immediately
    time.sleep(1)
    counter += 1
    hourly_counter += 1
    five_minute_counter += 1
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
        if time.strftime("%H:%M") > backup_time and not utils.is_backup_running() and not os.path.isfile(f"history/borg_errors_{date}.log"):
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

    
    ## CHECK IF WE NEED TO SHUTDOWN OR REBOOT #######################################################################

    automatic_shutdown_enabled = unix_config.get_value("AUTOMATIC_SHUTDOWN_ENABLED", "False") == "True"
    if automatic_shutdown_enabled:
        shutdown_type_is_reboot = unix_config.get_value("AUTOMATIC_SHUTDOWN_TYPE") == "Reboot"
        shutdown_time = unix_config.get_value("AUTOMATIC_SHUTDOWN_TIME", "00:00")
        shutdown_weekday = unix_config.get_value("AUTOMATIC_SHUTDOWN_WEEKDAY", "6")

        # Check if the current weekday is or it is set to daily
        # The weekday is a number from 0 to 6, where 0 is Monday and 6 is Sunday
        if shutdown_weekday == "daily" or shutdown_weekday == str(datetime.today().weekday()):

            # Check if we already did this action today
            last_date = ""
            if os.path.isfile("history/last_shutdown"):
                last_date = open("history/last_shutdown").read()
            current_date = datetime.now().strftime("%Y-%m-%d")
            if current_date != last_date.strip():

                # Shutdown time limit: the latest time the server will restart for this period. (1 hour after shutdown time)
                shutdown_time_limit = str(int(shutdown_time.split(":")[0]) + 1) + ":" + shutdown_time.split(":")[1]
                if len(shutdown_time_limit) == 4:
                    shutdown_time_limit = "0" + shutdown_time_limit
                if shutdown_time_limit.split(":")[0] == "24":
                    shutdown_time_limit = "00:" + shutdown_time_limit.split(":")[1]

                # If we are in the timeslot between shutdown_tuime and shutdown_time_limit, then shutdown:
                if datetime.now().strftime("%H:%M") >= shutdown_time and datetime.now().strftime("%H:%M") < shutdown_time_limit:
                    with open("history/last_shutdown") as file:
                        file.write(current_date)
                    if shutdown_type_is_reboot:
                        os.system("reboot")
                    else:   
                        os.system("shutdown now")


    ## CHECK IF SAMBA-AD-DC IS RUNNING ###############################################################################

    if not "samba-ad-dc" in subprocess.getoutput("systemctl list-units --type=service --state=running --no-legend --no-pager"):
        os.system("systemctl restart samba-ad-dc")

    ##################################################################################################################
    ## RUN EVERY 5 MINUTES ##########################################################################################
    ##################################################################################################################

    if five_minute_counter < 300:
        continue
    five_minute_counter = 0

    ## CHECK IF CPU, MEMORY IS TOO HIGH #############################################################################

    if utils.get_cpu_usage(five_min=True) > 80:
        os.system("curl -X POST -F 'subject=🖥️📈 CPU-Auslastung hoch📈' -F 'message=Die CPU-Auslastung des Servers ist zu hoch. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")

    if utils.get_ram_usage()["ram_percent"] > 80:
        os.system("curl -X POST -F 'subject=💾📈 RAM-Auslastung hoch📈' -F 'message=Die RAM-Auslastung des Servers ist zu hoch. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")

    ##################################################################################################################
    ## RUN EVERY HOUR ################################################################################################
    ##################################################################################################################

    if hourly_counter < 3600:
        continue
    hourly_counter = 0

    ## CHECK IF DISK SPACE IS LOW ####################################################################################
    disks = utils.get_disks_stats()
    for disk in disks:
        if int(disk["used_percent"]) > 90:
            os.system(f"curl -X POST -F 'subject=💿📈 Festplattenauslastung hoch📈' -F 'message=Die Festplattenauslastung des Servers ist zu hoch. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")

    ## Get list of upgradable packages
    os.system("apt list --upgradable > upgradable_packages")


    ## Ensure public key of root user is available 
    # If public key of root user is not available, create it
    if not os.path.isfile("/root/.ssh/id_rsa.pub"):
        os.system("ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ''")
    os.system("cp /root/.ssh/id_rsa.pub .")
    os.system("chmod 444 id_rsa.pub")
    