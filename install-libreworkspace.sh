#!/bin/bash
# This script is used from the .iso installation medium

set -e
sed -i '/cdrom:/d' /etc/apt/sources.list
apt-get update
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://repo.libre-workspace.org/gpg.key' | gpg --dearmor -o /usr/share/keyrings/libre-workspace-archive-keyring.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/libre-workspace-archive-keyring.gpg] https://repo.libre-workspace.org stable main' > /etc/apt/sources.list.d/libre-workspace-stable.list
apt-get update
apt-get install -y --allow-unauthenticated libre-workspace-portal
bash /usr/lib/libre-workspace/portal/prepare_for_first_boot.sh

# Disable this service so it doesn't run again
systemctl disable first-boot-setup.service
rm /etc/systemd/system/first-boot-setup.service
rm /root/install-libreworkspace.sh
reboot