# Called from root crontab every minute
import os
import unix # (its in the same directory)
import time

# If cron is not running as root, exit
if os.geteuid() != 0:
    print("Cron is not running as root. Exiting.")
    exit()

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



counter = 0
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
    unix.read_config_file()

    ## BACKUP ######################################################################################################

    # Get backup time from config file
    if unix.get_value("BORG_REPOSITORY") != "" and not os.path.exists("backup_disabled"):
        ensure_fingerprint_is_trusted()
        backup_time = unix.get_value("BORG_BACKUP_TIME")
        date = time.strftime("%Y-%m-%d")

        # If current time is higher than backup time, run backup
        if time.strftime("%H:%M") > backup_time and not os.path.isfile("backup_running") and not os.path.isfile(f"history/borg_errors_{date}.log"):
            print("Running backup")
            os.system("bash ./do_backup.sh")

    

    ## SYSTEM UPDATE ################################################################################################

    if os.path.isfile("update_system"):
        os.remove("update_system")
        print("Updating system")
        os.system("bash ./do_update.sh")

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
    