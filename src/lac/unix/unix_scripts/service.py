# Called from root crontab every minute
import os
import unix_config # (its in the same directory)
import time
from datetime import datetime
import subprocess
import utils
import requests

# If cron is not running as root, exit
if os.geteuid() != 0:
    print("Cron is not running as root. Exiting.")
    exit()

print("Running unix service...")

# Change current directory to the directory of this script
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# Get current directory
current_directory = os.getcwd()


# Let us get the environment of env.sh
env_file_path = "/usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh"
env = {}
lines = open(env_file_path).readlines()
for line in lines:
    line = line.strip()
    if line == "" or line.startswith("#"):
        continue
    line = line.replace("export ", "")
    key = line.split("=")[0]
    value = line.split("=")[1]
    env[key] = value

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

# In here the time for a last message is stored in seconds
last_message_sent = {}

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

    ##################################################################################################################
    ## RUN EVERY MINUTE ##############################################################################################
    ##################################################################################################################

    # Read config file
    unix_config.read_config_file()

    current_date = time.strftime("%Y-%m-%d")

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
    if time.strftime("%H:%M") > update_time and not os.path.isfile("maintenance/update_running") and not os.path.isfile(f"history/update-{current_date}.log"):
        print("Starting automatic updates")
        p = subprocess.Popen(["bash", "update_everything.sh"], cwd="maintenance")
        p.wait()

    
    ## RUN PATCHES ###################################################################################################

    # We run patches at the defined backup time (after the backups of course). It this is not defined, then we take 02:00 as default
    # We check if we had run the patches today already by checking the history folder (DATE-patch.log)
    patch_time = unix_config.get_value("BORG_BACKUP_TIME", "02:00")
    patch_log_path = f"history/patch-{current_date}.log"
    if time.strftime("%H:%M") > patch_time and not os.path.isfile(patch_log_path):
        print("Running patches")

        # Get all folders in /usr/share/linux-arbeitsplatz/unix/unix_scripts/
        possible_modules = os.listdir("/usr/share/linux-arbeitsplatz/unix/unix_scripts/")
        # Filter all folders which don't have a path like /root/[folder]
        # (Because we only want to run patches for installed modules or addons)
        possible_modules = [folder for folder in possible_modules if os.path.isdir(f"/root/{folder}") or folder == "nextcloud" or folder == "general"]
        # Make the paths absolute
        for i in range(len(possible_modules)):
            possible_modules[i] = f"/usr/share/linux-arbeitsplatz/unix/unix_scripts/{possible_modules[i]}"
                
        # Now do everything again for the addons folder:
        possible_addons = os.listdir("/usr/share/linux-arbeitsplatz/unix/unix_scripts/addons/")
        possible_addons = [folder for folder in possible_addons if os.path.isdir(f"/root/{folder}")]
        for i in range(len(possible_addons)):
            possible_addons[i] = f"/usr/share/linux-arbeitsplatz/unix/unix_scripts/addons/{possible_addons[i]}"

        possible_module_or_addon_folders = possible_modules + possible_addons

        # In this state also some other folders are in the list, so we need to filter all folders out wich don't have a patches folder
        possible_module_or_addon_folders = [folder for folder in possible_module_or_addon_folders if os.path.isdir(folder+"/patches")]
      

        # Now we have a list of all folders which have a patches folder
        # Let's get all patch.sh in all patches folders (absolute path)
        patch_files = []
        for folder in possible_module_or_addon_folders:
            patch_files += [folder+"/patches/"+file for file in os.listdir(folder+"/patches") if file.endswith(".sh")]

        # Now we have a list of all patch files
        # The Files have a DATE schema at the beginning of the filename
        # Sort the files by date (oldest first)
        patch_files.sort()
        # Run every patch file with cwd in the directory of the patch file
        for patch_file in patch_files:
            try:
                p = subprocess.Popen(["bash", patch_file], 
                                        cwd="/".join(patch_file.split("/")[:-1]), 
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        env=env)
                p.wait()
                # Get output of the patch file
                output = p.stdout.read().decode("utf-8") + p.stderr.read().decode("utf-8")
                # Write the output to the patch log file
                with open(patch_log_path, "a") as file:
                    file.write(f"Running {patch_file}:\n{output}\n\n")
                    file.close()
            except Exception as e:
                print(f"Error while running patch file {patch_file}: {e}")
                pass

    

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
        if shutdown_weekday == "daily" or str(shutdown_weekday) == str(datetime.today().weekday()):

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

                # If we are in the timeslot between shutdown_time and shutdown_time_limit, then shutdown:
                if datetime.now().strftime("%H:%M") >= shutdown_time and datetime.now().strftime("%H:%M") < shutdown_time_limit:
                    with open("history/last_shutdown", "w") as file:
                        file.write(current_date)
                        file.close()
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
        if not "cpu" in last_message_sent or time.time() - last_message_sent["cpu"] > 3600:
            last_message_sent["cpu"] = time.time()
            os.system("curl -X POST -F 'subject=🖥️📈 CPU-Auslastung hoch📈' -F 'message=Die CPU-Auslastung des Servers ist zu hoch. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")

    if utils.get_ram_usage()["ram_percent"] > 80:
        if not "ram" in last_message_sent or time.time() - last_message_sent["ram"] > 3600:
            last_message_sent["ram"] = time.time()
        os.system("curl -X POST -F 'subject=💾📈 RAM-Auslastung hoch📈' -F 'message=Die RAM-Auslastung des Servers ist zu hoch. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")

    ## CHECK EVERY DOMAIN IN CADDY CONFIG IF THE SPECIFIED SERVICE IS STILL WORKING ##################################

    caddy_config = open("/etc/caddy/Caddyfile").read()
    for line in caddy_config.split("\n"):
        if line.strip().startswith("#"):
            continue
        line = line.split("#")[0]
        words = line.split()
        # If the first word has two dots or one : in it, it is a domain we want to check
        if len(words) > 0 and (words[0].count(".") == 2 or words[0].count(":") == 1) and line.strip().endswith("{"):
            domain = words[0]
            # print(f"Checking domain {domain}")
            # Check if the domain is reachable and the code is not 200
            try:
                respose = requests.get(f"https://{domain}", verify=False)
                if respose.status_code != 200:
                    if not domain in last_message_sent or time.time() - last_message_sent[domain] > 3600:
                        last_message_sent[domain] = time.time()
                        os.system(f"curl -X POST -F 'subject=🌐❌ Domain {domain} nicht erreichbar❌' -F 'message=Die Domain {domain} ist nicht erreichbar. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")
            except:
                if not domain in last_message_sent or time.time() - last_message_sent[domain] > 3600:
                    last_message_sent[domain] = time.time()
                    os.system(f"curl -X POST -F 'subject=🌐❌ Domain {domain} nicht erreichbar❌' -F 'message=Die Domain {domain} ist nicht erreichbar. Bitte überprüfen Sie den Server.' localhost:11123/unix/send_mail")
    

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
    