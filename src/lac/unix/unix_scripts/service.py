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


counter = 0
while True:
    ## Run every minute ############################################################################################
    # If run_service file exists, remove it and run service immediately
    time.sleep(1)
    counter += 1
    if counter < 5 and not os.path.isfile("run_service"):
        continue
    if os.path.isfile("run_service"):
        os.remove("run_service")
    counter = 0
    if os.path.isfile("disabled"):
        print("Service is currently disabled.")
        continue

    # Read config file
    unix.read_config_file()

    ## ENSURE PUBLIC KEY OF ROOT USER IS AVAILABLE #################################################################
    # If public key of root user is not available, create it
    if not os.path.isfile("/root/.ssh/id_rsa.pub"):
        os.system("ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ''")
    os.system("cp /root/.ssh/id_rsa.pub .")
    os.system("chmod 444 id_rsa.pub")

    ## ENSURE SSH-FINGERPRINT OF BORG REPOSITORY IS KNOWN ##########################################################
    # Fingerprint is located in trusted_fingerprints file
    # If the fingerprints are not in the /root/.ssh/known_hosts file, add them
    if not os.path.isfile("/root/.ssh/known_hosts"):
        os.system("touch /root/.ssh/known_hosts")
    known_hosts = open("/root/.ssh/known_hosts").readlines()
    trusted_fingerprints = open("trusted_fingerprints").readlines()
    for fingerprint in trusted_fingerprints:
        if fingerprint not in known_hosts:
            known_hosts.append(fingerprint)
    # Write the fingerprints to the /root/.ssh/known_hosts file
    with open("/root/.ssh/known_hosts", "w") as f:
        f.writelines(known_hosts)


    ## BACKUP ######################################################################################################

    # Get backup time from config file
    backup_time = unix.config["BORG_BACKUP_TIME"]
    date = time.strftime("%Y-%m-%d")

    # If current time is higher than backup time, run backup
    if time.strftime("%H:%M") > backup_time and not os.path.isfile("backup_running") and not os.path.isfile(f"history/borg_errors_{date}.log"):
        print("Running backup")
        os.system("bash ./do_backup.sh")
