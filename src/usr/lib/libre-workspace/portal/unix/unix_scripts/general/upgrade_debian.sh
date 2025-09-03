#!/bin/bash

# Check if we are currently on bookworm
if ! grep -q 'bookworm' /etc/apt/sources.list; then
  echo "Not on bookworm. Skipping Debian Upgrade."
  exit 0
fi

# Check if we are root
if [ "$(id -u)" -ne 0 ]; then
  echo "Not running as root"
  exit 1
fi

# Stop all services:
. /usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/stop_services.sh

# Upgrade from bookworm to trixie

# Change everything from bookworm to trixie
sed -i 's/bookworm/trixie/g' /etc/apt/sources.list

# Also change everything from bookworm to trixie in all files in /etc/apt/sources.list.d/
sed -i 's/bookworm/trixie/g' /etc/apt/sources.list.d/*

apt update

DEBIAN_FRONTEND=noninteractive apt full-upgrade -y

# Autoremove
DEBIAN_FRONTEND=noninteractive apt autoremove -y

# Reinstall libre-workspace-portal (because venv of python gets destroyed)
DEBIAN_FRONTEND=noninteractive apt install --reinstall libre-workspace-portal -y

# Set PHP variables
. /usr/lib/libre-workspace/modules/nextcloud/set_php_variables.sh


# Launch a process in the background sleeping for 1h, then reboot
echo "Finished Debian Upgrade. Rebooting in 1 hour..."
( sleep 1h && reboot ) &

libre-workspace-send-mail "Debian Upgrade Finished. Reboot in one hour" "The Debian upgrade has been completed successfully. The system will reboot in one hour to finish the upgrade."