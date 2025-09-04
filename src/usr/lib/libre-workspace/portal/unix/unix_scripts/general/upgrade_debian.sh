#!/bin/bash

# Check if we are currently on bookworm
if ! grep -q 'bookworm' /etc/os-release; then
  echo "Not on bookworm. Skipping Debian Upgrade."
  exit 0
fi

# Remove fail2ban, redis and redis-server, Because they tend to cause issues during upgrades
DEBIAN_FRONTEND=noninteractive sudo apt remove redis redis-server -y
DEBIAN_FRONTEND=noninteractive sudo apt purge fail2ban -y

# Check if we are root
if [ "$(id -u)" -ne 0 ]; then
  echo "Not running as root"
  exit 1
fi

# Make sure we are up to date
DEBIAN_FRONTEND=noninteractive apt update
DEBIAN_FRONTEND=noninteractive apt full-upgrade -y -o Dpkg::Options::="--force-confold"
DEBIAN_FRONTEND=noninteractive apt autoremove -y

# Stop all services:
. /usr/lib/libre-workspace/portal/unix/unix_scripts/maintenance/stop_services.sh

# Upgrade from bookworm to trixie

# Change everything from bookworm to trixie
sed -i 's/bookworm/trixie/g' /etc/apt/sources.list

# Also change everything from bookworm to trixie in all files in /etc/apt/sources.list.d/
sed -i 's/bookworm/trixie/g' /etc/apt/sources.list.d/*

apt update

DEBIAN_FRONTEND=noninteractive apt full-upgrade -y -o Dpkg::Options::="--force-confold"

# Autoremove
DEBIAN_FRONTEND=noninteractive apt autoremove -y

# Reinstall libre-workspace-portal (because venv of python gets destroyed)
DEBIAN_FRONTEND=noninteractive apt install --reinstall libre-workspace-portal -y


# Check if php is installed:
if [ -f /usr/bin/php ]; then
  echo "PHP is installed. Reinstalling PHP packages."

  DEBIAN_FRONTEND=noninteractive sudo apt install php-curl -y

  # Set PHP variables
  . /usr/lib/libre-workspace/modules/nextcloud/set_php_variables.sh
fi

# Check if nextcloud is installed
if [ -d /var/www/nextcloud ]; then
  echo "Nextcloud is installed. Running maintenance script."
  sudo -u www-data php /var/www/nextcloud/occ upgrade
  sudo -u www-data php /var/www/nextcloud/occ app:update --all
  sudo -u www-data php /var/www/nextcloud/occ maintenance:mode --off
  DEBIAN_FRONTEND=noninteractive sudo apt install libmagickcore-7.q16-10-extra -y
fi

# If samba_dc should be installed, make sure it is still installed
if [ -d /root/samba_dc ]; then
  DEBIAN_FRONTEND=noninteractive sudo apt install samba-ad-dc -y
fi

# Ensure docker is installed if no official docker list exists
if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
  DEBIAN_FRONTEND=noninteractive sudo apt install apparmor docker.io docker-compose docker-cli -y
fi

# Install fail2ban, redis and redis-server
DEBIAN_FRONTEND=noninteractive sudo apt install  fail2ban redis redis-server -y -o Dpkg::Options::="--force-confold"

# Launch a process in the background sleeping for 1h, then reboot
echo "Finished Debian Upgrade. Rebooting in 1 hour..."
( sleep 1h && reboot ) &

libre-workspace-send-mail "Debian Upgrade Finished. Reboot in one hour" "The Debian upgrade has been completed successfully. The system will reboot in one hour to finish the upgrade."