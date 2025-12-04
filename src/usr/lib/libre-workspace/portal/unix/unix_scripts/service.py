import os
import unix_config # (its in the same directory)
import time
from datetime import datetime
import subprocess
import utils
import requests

# If cron is not running as root, exit
if os.geteuid() != 0:
    print("Service is not running as root. Exiting.")
    exit()

print("Running libre workspace service...")

# Let's get the environment of /etc/libre-workspace/libre-workspace.env
env_file_path = "/etc/libre-workspace/libre-workspace.env"
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

def ensure_fingerprint_is_trusted(additional_id=None):
    ## Ensure trusted SSH fingerprints are available
    # Fingerprint is located in trusted_fingerprints file
    # If the fingerprints are not in the /root/.ssh/known_hosts file, add them
    if additional_id:
        fingerprint_file = f"trusted_fingerprints_{additional_id}"
    else:
        fingerprint_file = "trusted_fingerprints"
    if not os.path.isfile("/root/.ssh/known_hosts"):
        os.system("touch /root/.ssh/known_hosts")
    known_hosts = open("/root/.ssh/known_hosts").readlines()
    if os.path.isfile(fingerprint_file):
        trusted_fingerprints = open(fingerprint_file).readlines()
        for fingerprint in trusted_fingerprints:
            if fingerprint not in known_hosts:
                known_hosts.append(fingerprint)
    # Write the fingerprints to the /root/.ssh/known_hosts file
    with open("/root/.ssh/known_hosts", "w") as f:
        f.writelines(known_hosts)


# Get lw admin token
def get_lw_admin_token():
    # Check if file exists: /var/lib/libre-workspace/local-admin-token
    if os.path.isfile("/var/lib/libre-workspace/local-admin-token"):
        # Read the token from the file
        with open("/var/lib/libre-workspace/local-admin-token", "r") as f:
            token = f.read().strip()
            token = token.split("=")[1]
        return token
    else:
        # If the file does not exist, return empty string
        return ""
    

## TODO: REMOVE IT IN 2026
def ensure_linux_arbeitsplatz_package_is_removed():
    # Check if the linux-arbeitsplatz package is installed
    if os.system("dpkg -l | grep linux-arbeitsplatz") == 0:
        # If it is installed, remove it
        os.system("apt remove -y linux-arbeitsplatz")
        # Remove the package from the list of installed packages
        os.system("apt autoremove -y")
    
    # Check if libre-workspace-service.service is not enabled
    if os.system("systemctl is-enabled libre-workspace-service.service") != 0:
        # Also ensure that the services for the new libre workspace portal are running
        os.system("systemctl enable --now libre-workspace-portal.service")
        os.system("systemctl enable --now libre-workspace-service.service")


def check_caddy_running_and_rescue():
    # Check if Caddy is running. If Caddy is not running, try to load the backup if a backup exists and the backup is not older than 3 hours.
    if not utils.is_caddy_running():
        print("Caddy is not running. Trying to load backup...")
        # Check if the backup file exists
        backup_file = "/etc/caddy/Caddyfile.backup.libreworkspace"
        if os.path.isfile(backup_file):
            # Check if the backup file is older than 3 hours
            backup_mtime = os.path.getmtime(backup_file)
            current_time = time.time()
            if current_time - backup_mtime < 10800:
                # If the backup file is not older than 3 hours, copy it to the Caddyfile
                print("Backup file found and is not older than 3 hours. Restoring backup...")
                os.system(f"cp {backup_file} /etc/caddy/Caddyfile")
                # Restart Caddy
                os.system("systemctl restart caddy")


def check_other_important_system_services_running():
    important_services = ["samba-ad-dc", "caddy", "libre-workspace-portal", "mariadb", "redis-server", "tftpd-hpa"]
    for service in important_services:
        # Check if service exists and is not running
        try:
            if os.system(f"systemctl is-enabled {service}") == 0 and os.system(f"systemctl is-active {service}") != 0:
                print(f"Service {service} is not running. Restarting...")
                os.system(f"systemctl restart {service}")
        except Exception as e:
            print(f"An error occurred while checking service {service}: {e}")


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
    if os.path.isfile("/var/lib/libre-workspace/portal/run_service"):
        os.remove("/var/lib/libre-workspace/portal/run_service")
        counter = 60
        hourly_counter = 3600
    if counter < 60:
        continue
    counter = 0

    ##################################################################################################################
    ## RUN EVERY MINUTE ##############################################################################################
    ##################################################################################################################

    ## CHECK IF LINUX ARBEITSPLATZ PACKAGE IS INSTALLED ###############################################################
    ## TODO: REMOVE IT IN 2026
    ensure_linux_arbeitsplatz_package_is_removed()

    check_other_important_system_services_running()

    # Read config file
    unix_config.read_config_file()

    current_date = time.strftime("%Y-%m-%d")

    lw_admin_token = get_lw_admin_token()
    if lw_admin_token == "":
        print("No local admin token. Can't send emails.")

    # Check if Caddy is running. If not try to get the backup of the Caddyfile entry.
    check_caddy_running_and_rescue()

    ## BACKUP ######################################################################################################

    # Get backup time from config file
    if unix_config.get_value("BORG_REPOSITORY") != "" and not os.path.exists("/var/lib/libre-workspace/portal/backup_disabled"):
        ensure_fingerprint_is_trusted()
        backup_time = unix_config.get_value("BORG_BACKUP_TIME")
        date = time.strftime("%Y-%m-%d")

        # If current time is higher than backup time, run backup
        if time.strftime("%H:%M") > backup_time and not utils.is_backup_running() and not os.path.isfile(f"/var/lib/libre-workspace/portal/history/borg_errors_{date}.log"):
            print("Running backup")
            # Run do_backup.sh script with cwd in the maintenance directory
            p = subprocess.Popen(["bash", "do_backup.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/")
            p.wait()


            # Send email to admin if backup failed
            read_errors = open(f"/var/lib/libre-workspace/portal/history/borg_errors_{date}.log").read()
            if read_errors.strip() != "":
                # Full path of the log file:
                log_file = os.path.abspath(f"/var/lib/libre-workspace/portal/history/borg_errors_{date}.log")
                os.system(f"curl -X POST -F 'subject=💾❌ Backup completed with errors❌' -F 'message=Today's backup was not fully successful.\nAttached you will find the error messages.' -F 'attachment_path={log_file}' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")
    
    ## ADDITIONAL_BACKUPS ###########################################################################################

    for folder in os.listdir("/var/lib/libre-workspace/portal/"):
        folder = folder.split("/")[-1]
        if "additional_backup_" in folder:
            additional_id = folder.replace("additional_backup_", "")
            key_addition = ""
            if additional_id:
                key_addition = "_" + additional_id
                history_folder = "/var/lib/libre-workspace/portal/" + folder
            if unix_config.get_value("BORG_REPOSITORY"+key_addition) != "" and not os.path.exists("/var/lib/libre-workspace/portal/backup_disabled"+key_addition):
                ensure_fingerprint_is_trusted(additional_id)
                backup_time = unix_config.get_value("BORG_BACKUP_TIME"+key_addition)
                date = time.strftime("%Y-%m-%d")
                backup_name = unix_config.get_value("ADDITIONAL_BACKUP_NAME"+key_addition, "Additional Backup")

                # If current time is higher than backup time, run backup
                if time.strftime("%H:%M") > backup_time and not utils.is_backup_running() and not os.path.isfile(f"{history_folder}/borg_errors_{date}.log"):
                    print("Running backup")
                    # Run do_backup.sh script with cwd in the maintenance directory
                    p = subprocess.Popen(["bash", "do_backup.sh", additional_id], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/")
                    p.wait()


                    # Send email to admin if backup failed
                    read_errors = open(f"{history_folder}/borg_errors_{date}.log").read()
                    if read_errors.strip() != "":
                        # Full path of the log file:
                        log_file = os.path.abspath(f"{history_folder}/borg_errors_{date}.log")
                        os.system(f"curl -X POST -F 'subject=💾❌ Backup: {backup_name} completed with errors❌' -F 'message=Today's backup ({backup_name}) was not fully successful.\nAttached you will find the error messages.' -F 'attachment_path={log_file}' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")

    ## SYSTEM UPDATE ################################################################################################

    # If a user manually requested an update, run update
    if os.path.isfile("/var/lib/libre-workspace/portal/update_system"):
        os.remove("/var/lib/libre-workspace/portal/update_system")
        print("Updating system")
        p = subprocess.Popen(["bash", "do_update.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/")

    # All other updates:
    update_time = unix_config.get_value("UPDATE_TIME", "02:00")
    if time.strftime("%H:%M") > update_time and not os.path.isfile("/var/lib/libre-workspace/portal/update_running") and not os.path.isfile(f"/var/lib/libre-workspace/portal/history/update-{current_date}.log"):
        print("Starting automatic updates")
        p = subprocess.Popen(["bash", "update_everything.sh"], cwd="/usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/")
        p.wait()

    
    ## RUN PATCHES ###################################################################################################

    # We run patches at the defined backup time (after the backups of course). If this is not defined, then we take 02:00 as default
    # We check if we had run the patches today already by checking the history folder (DATE-patch.log)
    patch_time = unix_config.get_value("BORG_BACKUP_TIME", "02:00")
    patch_log_path = f"/var/lib/libre-workspace/portal/history/patch-{current_date}.log"
    if time.strftime("%H:%M") > patch_time and not os.path.isfile(patch_log_path):
        print("Running patches")

        # Get all folders in /usr/lib/libre-workspace/modules/
        possible_modules = os.listdir("/usr/lib/libre-workspace/modules/")
        # Filter all folders which don't have a path like /root/[folder]
        # (Because we only want to run patches for installed modules or addons)
        possible_modules = [folder for folder in possible_modules if os.path.isdir(f"/root/{folder}") or folder == "nextcloud" or folder == "general" or folder == "samba_dc" ]
        # Make the paths absolute
        for i in range(len(possible_modules)):
            possible_modules[i] = f"/usr/lib/libre-workspace/modules/{possible_modules[i]}"
                
        # Now do everything again for the addons folder:
        possible_addons = os.listdir("/usr/lib/libre-workspace/modules/")
        possible_addons = [folder for folder in possible_addons if os.path.isdir(f"/root/{folder}")]
        for i in range(len(possible_addons)):
            possible_addons[i] = f"/usr/lib/libre-workspace/modules/{possible_addons[i]}"

        possible_module_or_addon_folders = possible_modules + possible_addons

        # In this state also some other folders are in the list, so we need to filter all folders out which don't have a patches folder
        possible_module_or_addon_folders = [folder for folder in possible_module_or_addon_folders if os.path.isdir(folder+"/patches")]
        possible_module_or_addon_folders.append("/usr/lib/libre-workspace/portal/unix/unix_scripts/general/patches")        

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
            if os.path.isfile("/var/lib/libre-workspace/portal/history/last_shutdown"):
                last_date = open("/var/lib/libre-workspace/portal/history/last_shutdown").read()
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
                    with open("/var/lib/libre-workspace/portal/history/last_shutdown", "w") as file:
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

    if utils.get_cpu_usage(five_min=True) >  int(unix_config.get_value("CPU_WARNING_THRESHOLD", 80)):
        if not "cpu" in last_message_sent or time.time() - last_message_sent["cpu"] > 3600:
            last_message_sent["cpu"] = time.time()
            os.system(f"curl -X POST -F 'subject=🖥️📈 High CPU Usage📈' -F 'message=The CPU usage of the server is too high. Please check the server.' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")

    if utils.get_ram_usage()["ram_percent"] > int(unix_config.get_value("RAM_WARNING_THRESHOLD", 80)):
        if not "ram" in last_message_sent or time.time() - last_message_sent["ram"] > 3600:
            last_message_sent["ram"] = time.time()
        os.system(f"curl -X POST -F 'subject=💾📈 High RAM Usage📈' -F 'message=The RAM usage of the server is too high. Please check the server.' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")

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

            if domain in unix_config.get_value("ONLINE_DETECTION_IGNORED_DOMAINS", "").split(","):
                continue

            # print(f"Checking domain {domain}")
            # Check if the domain is reachable and the code is not 200
            try:
                response = requests.get(f"https://{domain}", verify=False)
                if response.status_code >= 400:
                    if not domain in last_message_sent or time.time() - last_message_sent[domain] > 3600:
                        last_message_sent[domain] = time.time()
                        with open(f"/tmp/{domain}_response.txt", "w") as f:
                            f.write(response.text)
                        os.system(f"curl -X POST -F 'subject=🌐❌ Domain {domain} not reachable❌' -F 'message=The domain {domain} is not reachable. Please check the server.' -F 'attachment_path=/tmp/{domain}_response.txt' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")
            except requests.exceptions.RequestException as e:
                if not domain in last_message_sent or time.time() - last_message_sent[domain] > 3600:
                    last_message_sent[domain] = time.time()
                    with open(f"/tmp/{domain}_response.txt", "w") as f:
                        f.write(str(e))
                    os.system(f"curl -X POST -F 'subject=🌐❌ Domain {domain} not reachable❌' -F 'message=The domain {domain} is not reachable. Please check the server.' -F 'attachment_path=/tmp/{domain}_response.txt' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")
    
    
    ##################################################################################################################
    ## RUN EVERY HOUR ################################################################################################
    ##################################################################################################################

    if hourly_counter < 3600:
        continue
    hourly_counter = 0

    ## CHECK IF DISK SPACE IS LOW ####################################################################################
    disks = utils.get_disks_stats()
    for disk in disks:
        if int(disk["used_percent"]) > int(unix_config.get_value("DISK_WARNING_THRESHOLD", 90)):
            os.system(f"curl -X POST -F 'subject=💿📈 High Disk Usage📈' -F 'message=The disk usage of the server is too high. Please check the server.' -F 'lw_admin_token={lw_admin_token}' localhost:11123/unix/send_mail")

    ## Get list of upgradable packages
    os.system("apt list --upgradable > /var/lib/libre-workspace/portal/upgradable_packages")


    ## Ensure public key of root user is available 
    # If public key of root user is not available, create it
    if not os.path.isfile("/root/.ssh/id_rsa.pub"):
        os.system("ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ''")
    os.system("cp /root/.ssh/id_rsa.pub /var/lib/libre-workspace/portal/")
    os.system("chmod 440 /var/lib/libre-workspace/portal/id_rsa.pub")