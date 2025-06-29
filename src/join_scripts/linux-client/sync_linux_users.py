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
                return_value.append(linux_user)
            return return_value
        else:
            print(f"Failed to fetch Linux users. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching Linux users: {e}")


def add_user_to_group(username, group):
    """
    Adds a user to a specified group.
    """
    print(f"Adding user {username} to group {group}...")
    os.system(f"usermod -aG {group} {username}")


def remove_user_from_group(username, group):
    """
    Removes a user from a specified group.
    """
    print(f"Removing user {username} from group {group}...")
    os.system(f"deluser {username} {group}")


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
    
    # Check if the user is enabled
    enabled = user.get('enabled', True)
    if not enabled:
        print(f"Disabling user: {username}")
        os.system(f"usermod -L {username}")
    else:
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

    # Update Display Name
    display_name = user.get('display_name', '')
    if display_name:
        os.system(f"usermod -c '{display_name}' {username} 1>/dev/null 2>&1")


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


def get_all_groups_above_gid(gid):
    """
    Returns a list of all groups with GID above the specified value.
    """
    groups = []
    try:
        output = os.popen(f"getent group | awk -F: '$3 > {gid} {{print $1}}'").read().strip()
        groups = output.split('\n') if output else []
    except Exception as e:
        print(f"An error occurred while fetching groups: {e}")
    
    return groups


def apply_group_changes(user, groups):
    """
    Applies group changes for a user based on the provided groups.
    Adds the user to new groups and removes them from groups they are no longer part of.
    """
    current_groups = os.popen(f"groups {user}").read().strip().split(': ')[1].split()
    
    # Add new groups
    for group in groups:
        if group not in current_groups:
            add_user_to_group(user, group)
    
    # Remove from groups no longer present
    for group in current_groups:
        if group not in groups:
            # Only remove him from the group if it is not a system group
            if group in get_all_groups_above_gid(1000000):  
                remove_user_from_group(user, group)

def create_or_update_group(group):
    """
    Creates or updates a group based on the provided group data.
    """
    group_name = group.get('cn')
    gid = group.get('gidNumber')

    if not group_name or not gid:
        print(f"Invalid group data: {group}")
        return
    
    # Check if group already exists
    existing_group = os.popen(f"getent group {group_name}").read().strip()
    
    if not existing_group:
        print(f"Creating group: {group_name}")
        os.system(f"groupadd -g {gid} {group_name}")
    else:
        print(f"Updating group: {group_name}")
        os.system(f"groupmod -g {gid} {group_name}")


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


    # Get all groups we need to create or update
    all_online_groups = []
    for linux_user in linux_users:
        for group in linux_user.get('groups', []):
            group_already_exists = False
            for online_group in all_online_groups:
                if online_group['cn'] == group['cn']:
                    group_already_exists = True
                    break
            if not group_already_exists:
                all_online_groups.append(group)
    
    for group in all_online_groups:
        create_or_update_group(group)

    for linux_user in linux_users:
        update_or_create_linux_user(linux_user)
        apply_group_changes(linux_user['username'], [group['cn'] for group in linux_user.get('groups', [])])

    # Remove users that are not in the portal anymore
    all_local_users = get_all_users_above_uid(10000)  # Assuming UIDs below 1000 are system users
    for local_user in all_local_users:
        if local_user not in [user['username'] for user in linux_users]:
            print(f"User {local_user} is not in the portal (anymore), removing...")
            os.system(f"deluser {local_user} --remove-home")

    # Remove groups that are not in the portal anymore
    all_local_groups = get_all_groups_above_gid(1000000)  # Assuming GIDs below 1000 are system groups
    for local_group in all_local_groups:
        if local_group not in [group['cn'] for group in all_online_groups]:
            print(f"Group {local_group} is not in the portal (anymore), removing...")
            os.system(f"groupdel {local_group}")

