#!/bin/bash

# /usr/share/linux-arbeitsplatz/unix/unix_scripts/addons/*  -> /usr/lib/libre-workspace/modules/
# /usr/share/linux-arbeitsplatz/cfg -> /etc/libre-workspace/portal/portal.conf
# /usr/share/linux-arbeitsplatz/unix/unix_scripts/unix.conf ->  /etc/libre-workspace/libre-workspace.conf
# /usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh ->  /etc/libre-workspace/libre-workspace.env
# /usr/share/linux-arbeitsplatz/unix/unix_scripts/history/ -> /var/lib/libre-workspace/portal/history
# /usr/share/linux-arbeitsplatz/db.sqlite3 -> /var/lib/libre-workspace/portal/
# /usr/share/linux-arbeitsplatz/media/ -> /var/lib/libre-workspace/portal/
# /usr/share/linux-arbeitsplatz/unix/unix_scripts/app_dashboard_settings.json -> /var/lib/libre-workspace/portal/app_dashboard_settings.json

# Check if the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
fi


# Check if the script has been run before
if [ -f /var/lib/libre-workspace/.migrated_to_new_folderstructure_2025 ]; then
    echo "Migration has already been performed. Exiting."
    exit 0
fi

# Stop libre-workspace services
systemctl stop libre-workspace-portal.service
systemctl stop libre-workspace-service.service

# Also try to stop the old services if they exist
systemctl stop linux-arbeitsplatz-web.service
systemctl stop linux-arbeitsplatz-unix.service



# Define source and destination directories in arrays
source_array=(
    "/usr/share/linux-arbeitsplatz/unix/unix_scripts/addons/*"
    "/usr/share/linux-arbeitsplatz/cfg"
    "/usr/share/linux-arbeitsplatz/unix/unix_scripts/unix.conf"
    "/usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh"
    "/usr/share/linux-arbeitsplatz/unix/unix_scripts/history/"
    "/usr/share/linux-arbeitsplatz/db.sqlite3"
    "/usr/share/linux-arbeitsplatz/media/"
    "/usr/share/linux-arbeitsplatz/unix/unix_scripts/app_dashboard_settings.json"
)

destination_array=(
    "/usr/lib/libre-workspace/modules/"
    "/etc/libre-workspace/portal/portal.conf"
    "/etc/libre-workspace/libre-workspace.conf"
    "/etc/libre-workspace/libre-workspace.env"
    "/var/lib/libre-workspace/portal/history/"
    "/var/lib/libre-workspace/portal/db.sqlite3"
    "/var/lib/libre-workspace/portal/media/"
    "/var/lib/libre-workspace/portal/app_dashboard_settings.json"
)

# Loop through the arrays and copy files/directories if they don't already exist at the destination
for i in "${!source_array[@]}"; do
    source="${source_array[$i]}"
    destination="${destination_array[$i]}"

    # Create destination directory if it doesn't exist
    mkdir -p "$(dirname "$destination")"

    # Check if the source exists
    if [ -e $source ] || [ -L $source ]; then
        # Copy the source to the destination if it doesn't already exist
        if [ ! -e "$destination" ]; then
            # Use cp -r for directories, cp for files
            if [ -d $source ]; then
                cp -ra "$source" "$destination"
            else
                cp -a "$source" "$destination"
            fi
            echo "Copied $source to $destination"
        else
            echo "Destination $destination already exists, skipping $source"
        fi
    else
        echo "Source $source does not exist, skipping"
    fi
done

# Create a file to indicate that the migration has been performed
touch /var/lib/libre-workspace/.migrated_to_new_folderstructure_2025
echo "Migration to new folder structure completed successfully."

# Start libre-workspace services
systemctl start libre-workspace-portal.service
systemctl start libre-workspace-service.service
# We don't start the old services anymore, they are deprecated :)
