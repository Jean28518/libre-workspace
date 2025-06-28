#!/bin/python3

import os
import requests

LIBRE_WORKSPACE_URL="https://portal.int.de/"
API_KEY=""


def fetch_linux_users_from_api():
    """
    Syncs the Linux users with the Libre Workspace portal.
    """
    headers = {
        'Api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            f"{LIBRE_WORKSPACE_URL}api/linux_users/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            linux_users = response.json()
            return_value = []
            for linux_user in linux_users:
                if linux_user.get('enabled'):
                    return_value.append(linux_user)
            return return_value
        else:
            print(f"Failed to fetch Linux users. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching Linux users: {e}")


def update_or_create_linux_user(user):
    """
    Updates or creates a Linux user based on the provided user data.
    """
    username = user.get('username')
    uid = user.get('uidNumber')
    yescrypt_hash = user.get('yescrypt_hash')

    if not username or not uid or not yescrypt_hash:
        print(f"Invalid user data: {user}")
        return
    
    # Check if user already exists
    existing_user = os.popen(f"id -u {username} 2>/dev/null").read().strip()
    # If not create it:
    if not existing_user:
        print(f"Creating user: {username}")
        os.system(f"adduser --quiet --uid {uid} {username} --disabled-password --allow-bad-names --gecos ''")

    # Set the user's password using yescrypt hash
    print(f"Updating password for user: {username}")
    os.system(f"echo '{username}:{yescrypt_hash}' | chpasswd --encrypted")
    
    # Make sure user is enabled:
    os.system(f"usermod -U {username}")

    # Update sudo membership based on admin status
    if user.get('admin'):
        sudo_check = "sudo" in os.popen(f"groups {username}").read()
        if not sudo_check:
            print(f"Adding user {username} to the sudo group...")
            os.system(f"usermod -aG sudo {username}")
    else:
        # Check if user is in sudo group and remove if not admin
        sudo_check = "sudo" in os.popen(f"groups {username}").read()
        if sudo_check:
            # User is in sudo group, remove them
            print(f"Removing user {username} from the sudo group...")
            os.system(f"deluser {username} sudo")


def disable_linux_user(username):
    """
    Disables a Linux user by locking their account.
    """
    print(f"Disabling user: {username}")
    os.system(f"usermod -L {username}")
    

def get_all_users_above_uid(uid):
    """
    Returns a list of all users with UID above the specified value.
    Doesnt return the user nobody, as this is a system user.
    """
    users = []
    try:
        output = os.popen(f"getent passwd | awk -F: '$3 > {uid} {{print $1}}'").read().strip()
        users = output.split('\n') if output else []
    except Exception as e:
        print(f"An error occurred while fetching users: {e}")

    # Filter out the 'nobody' user if it exists
    if 'nobody' in users:
        users.remove('nobody')
    
    return users


def is_this_root():
    """
    Checks if the script is run as root.
    """
    return os.geteuid() == 0


if __name__ == "__main__":
    if os.environ.get("LIBRE_WORKSPACE_URL"):
        LIBRE_WORKSPACE_URL = os.environ["LIBRE_WORKSPACE_URL"]
    
    if os.environ.get("API_KEY"):
        API_KEY = os.environ["API_KEY"]

    if not is_this_root():
        print("This script must be run as root.")
        exit(1)

    linux_users = fetch_linux_users_from_api()

    for linux_user in linux_users:
        update_or_create_linux_user(linux_user)

    all_local_users = get_all_users_above_uid(10000)  # Assuming UIDs below 1000 are system users
    for local_user in all_local_users:
        if local_user not in [user['username'] for user in linux_users]:
            print(f"User {local_user} is not in the portal (anymore), disabling...")
            disable_linux_user(local_user)

