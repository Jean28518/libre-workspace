#!/bin/bash

# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD

docker-compose -f /root/desktop/docker-compose.yml down --volumes

apt purge task-cinnamon-desktop xrdp -y
apt autoremove --purge -y

rm -rf /root/desktop

# Remove the entry from /etc/hosts
sed -i "/desktop.$DOMAIN/d" /etc/hosts

# Remove the DNS entry
samba-tool dns delete la.$DOMAIN $DOMAIN desktop A $IP -Uadministrator%$ADMIN_PASSWORD

# Remove the Caddy entry
python3 ../remove_caddy_service.py desktop.$DOMAIN
systemctl reload caddy

ufw delete allow from 192.168.0.0/16 to any port 3389


# Remove the OIDC client
# TODO