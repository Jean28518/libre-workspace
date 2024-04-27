import os
import sys
import argparse
import requests
import subprocess
import time

# Add in the future:
# - Install Thunderbird addon cardbook
# - Add addressbooks to Thunderbird if available

def create_web_starter_file(name, icon, comment, link):
    desktop_file = f"""[Desktop Entry]
Name={name} (Libre Workspace)
Exec=xdg-open {link}
Icon={icon}
Type=Application
Categories=Network
Comment={comment}
"""
    filename = link.replace("https://", "").replace("http://", "").replace("/", "_")
    filename = "lw_" + filename
    with open(f"{os.getenv('HOME')}/.local/share/applications/{filename}.desktop", "w") as file:
        file.write(desktop_file)

def create_web_starters_in_menu(address):

    # Ensure https://
    if not address.startswith("http"):
        address = f"https://{address}"

    # Get all available services from libre workspace per api call
    json = requests.get(f"{address}/entries_json", verify=False).json()
    # Ensure .local/share/icons exists
    os.makedirs(f"{os.getenv('HOME')}/.local/share/icons", exist_ok=True)#

    for entry in json:
        # Download icon to .local/share/icons
        icon_url = address + entry["icon_url"]
        icon_name = icon_url.split("/")[-1]
        icon_path = f"{os.getenv('HOME')}/.local/share/icons/{icon_name}"
        with open(icon_path, "wb") as file:
            file.write(requests.get(icon_url).content)
        
        # Create Browser starters
        create_web_starter_file(entry["title"], icon_path, entry["description"], entry["link"])

        if "nextcloud" in entry["title"].lower() or "cloud" in entry["title"].lower():
            # Create Nextcloud starters
            for app in entry["nextcloud_apps"]:
                entry_link = entry["link"]
                app_icon_url = f"{entry_link}/apps/{app}/img/{app}.svg"
                app_icon_name = f"nextcloud_{app}.svg"
                app_icon_path = f"{os.getenv('HOME')}/.local/share/icons/{app_icon_name}"
                with open(app_icon_path, "wb") as file:
                    file.write(requests.get(app_icon_url).content)
                app_link = f"{entry['link']}/index.php/apps/{app}"
                app_name = app.capitalize()
                create_web_starter_file(f"{app_name}", app_icon_path, f"Starte {app} (Nextcloud)", app_link)  


def get_nextcloud_address(address):
    # Get nextcloud address:
    json = requests.get(f"{address}/entries_json", verify=False).json()
    nextcloud_address = ""
    for entry in json:
        if "nextcloud" in entry["title"].lower() or "cloud" in entry["title"].lower():
            nextcloud_address = entry["link"]
            break
    return nextcloud_address

def add_nextcloud_sync_client(address, username, password):
    # Create /.local/bin/
    os.makedirs(f"{os.getenv('HOME')}/.local/bin", exist_ok=True)

    version= requests.get("https://api.github.com/repos/nextcloud/desktop/releases/latest").json()["tag_name"]
    # Remove the v from the version
    version = version[1:]
    nextcloud_client_appimage_path = f"{os.getenv('HOME')}/.local/bin/Nextcloud-{version}-x86_64.AppImage"

    # Check if nextcloud client appimage already exists
    if os.path.exists(nextcloud_client_appimage_path):
        print("Nextcloud client appimage already exists")
    else:
        print("Downloading Nextcloud client appimage")
        # Get the latest nextcloud client appimage version

        # Download nextcloud client appimage
        nextcloud_client_appimage_download = f"https://download.nextcloud.com/desktop/releases/Linux/Nextcloud-{version}-x86_64.AppImage"
        with open(nextcloud_client_appimage_path, "wb") as file:
            file.write(requests.get(nextcloud_client_appimage_download).content)

        # Make the appimage executable
        os.chmod(nextcloud_client_appimage_path, 0o755)

    # Add nextcloud client appimage to autostart
    # (Nextcloud adds itself to autostart, so this is not necessary)
    nextcloud_address = get_nextcloud_address(address)
    
    
    # Ensure that no / is at the end of the nextcloud address
    if nextcloud_address.endswith("/"):
        nextcloud_address = nextcloud_address[:-1]
    
    # Check if already an account exists in Nextcloud config if this file is available.
    if os.path.exists(f"{os.getenv('HOME')}/.config/Nextcloud/nextcloud.cfg"):
        with open(f"{os.getenv('HOME')}/.config/Nextcloud/nextcloud.cfg") as file:
            if nextcloud_address in file.read():
                print("Nextcloud account already exists, skipping login")
                return

    # Login into nextcloud client
    os.system(f"{nextcloud_client_appimage_path} --serverurl {nextcloud_address} --userid {username} --apppassword {password}")
    # Keep nextcloud client running
    os.system(f"{nextcloud_client_appimage_path} &")


def login_to_gnome_online_accounts(address, username, password):
    nextcloud_address = get_nextcloud_address(address)
    print("Login to Gnome Online Accounts")
    address_without_protocol = nextcloud_address.replace("https://", "").replace("http://", "")
    # Ensure that a / is at the end of the nextcloud address
    if not nextcloud_address.endswith("/"):
        nextcloud_address += "/"

    unix_timestamp = int(time.time())
    goa_index = 1
    # Get how many accounts are already in the file
    if os.path.exists(f"{os.getenv('HOME')}/.config/goa-1.0/accounts.conf"):
        with open(f"{os.getenv('HOME')}/.config/goa-1.0/accounts.conf") as file:
            for line in file:
                if line.startswith("[Account"):
                    goa_index += 1
    goa_identity = f"account_{unix_timestamp}_{goa_index}"
    
    # We need to add an account to .config/goa-1.0/accounts.conf
    new_accounts_entry = f"""[Account {goa_identity}]
Provider=owncloud
Identity={username}
PresentationIdentity={username}@{address_without_protocol}
CalendarEnabled=true
ContactsEnabled=true
FilesEnabled=true
Uri={nextcloud_address}
AcceptSslErrors=false
"""
    # Check if the account is already in the file:
    if os.path.exists(f"{os.getenv('HOME')}/.config/goa-1.0/accounts.conf"):
        with open(f"{os.getenv('HOME')}/.config/goa-1.0/accounts.conf") as file:
            if f"{username}@{address_without_protocol}" in file.read():
                print("Account already exists, skipping login")
                return

    # Be aware, that there can be already some accounts in the file
    with open(f"{os.getenv('HOME')}/.config/goa-1.0/accounts.conf", "a") as file:
        file.write(new_accounts_entry)

    # Now we need to add the password to the keyring, if secret-tool is available
    if os.path.exists("/usr/bin/secret-tool"):
        # Put password via stdin to secret-tool. In the End we need to put EOF to stdin
        subprocess.run(["secret-tool", "store", "--label=owncloud", "goa-identity", f"owncloud:gen0:{goa_identity}"], input="{'password': <'" + password + "'>}", text=True, check=True)


def install_lan_crt(address):
    if not "int.de" in address:
        return
    print("Installing lan.crt to system, firefox, chrome and thunderbird...")
    # Download cert.int.de/lan.crt and trust the certificate
    os.system("wget https://cert.int.de/lan.crt -O /tmp/lan.crt --no-check-certificate")

    # Check if the certificate is really a certificate
    if not "BEGIN CERTIFICATE" in open("/tmp/lan.crt").read():
        print("No certificate found in lan.crt, skipping installation of lan.crt")
        return

    # Trust the certificate in the system (run as root)
    with open("/tmp/install_lan_crt.sh", "w") as file:
        file.write("""#!/bin/bash
cp /tmp/lan.crt /usr/local/share/ca-certificates/lan.crt
update-ca-certificates
# Also ensure that the certificate is trusted in Firefox, Chrome and Thunderbird. For this we need to install libnss3-tools
apt install libnss3-tools -y
""")
    os.system("pkexec bash /tmp/install_lan_crt.sh")

    # Trust the certificate in Firefox and Thunderbird and Chrome
    certificateFile = "/tmp/lan.crt"
    certificateName = "LAN"
    for certDB in subprocess.getoutput("find  ~/.mozilla* ~/.thunderbird ~/.pki -name 'cert9.db'").split("\n"):
        certDir = os.path.dirname(certDB)
        os.system(f"certutil -A -n '{certificateName}' -t 'TCu,Cuw,Tuw' -i {certificateFile} -d {certDir}")
    

argparser = argparse.ArgumentParser(description='Join a libre workspace')
argparser.add_argument('address', help='The address of the libre workspace')
argparser.add_argument('--username', required=False, help='The username for the libre workspace')
argparser.add_argument('--password', required=False, help='The password for the libre workspace')
argparser.add_argument('--create_web_entries', required=False, default="True", help='Create web entries in menu')
argparser.add_argument('--add_nextcloud_sync_client', required=False, default="True", help='Add nextcloud sync client')
argparser.add_argument('--install_lan_crt', required=False, default="True", help='Install lan.crt')
args = argparser.parse_args()

address = args.address
username = args.username
password = args.password
create_web_entries = args.create_web_entries
nextcloud_sync_client = args.add_nextcloud_sync_client
install_lan_crt = args.install_lan_crt

if create_web_entries == "True":
    create_web_starters_in_menu(address)

if nextcloud_sync_client == "True" and username and password:
    add_nextcloud_sync_client(address, username, password)

if address and username and password:
    login_to_gnome_online_accounts(address, username, password)

if address and install_lan_crt == "True":
    install_lan_crt(address)
