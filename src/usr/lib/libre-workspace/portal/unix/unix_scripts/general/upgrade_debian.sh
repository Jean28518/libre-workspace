#!/bin/bash

# Check if we are currently on bookworm
if ! grep -q 'bookworm' /etc/apt/sources.list; then
  echo "Not on bookworm"
  exit 1
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

apt update

DEBIAN_FRONTEND=noninteractive apt full-upgrade -y

# Autoremove
DEBIAN_FRONTEND=noninteractive apt autoremove -y

# Reinstall libre-workspace-portal (because venv of python gets destroyed)
DEBIAN_FRONTEND=noninteractive apt install --reinstall libre-workspace-portal -y

# Set PHP variables
. /usr/lib/libre-workspace/modules/nextcloud/set_php_variables.sh

reboot