#!/bin/bash

# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD

docker-compose -f /root/desktop/docker-compose.yml down --volumes


DEBIAN_FRONTEND=noninteractive apt purge task-cinnamon-desktop xrdp -y
DEBIAN_FRONTEND=noninteractive apt autoremove --purge -y

rm -rf /root/desktop

# Remove the entry from /etc/hosts
sed -i "/desktop.$DOMAIN/d" /etc/hosts

# Remove the DNS entry
samba-tool dns delete la.$DOMAIN $DOMAIN desktop A $IP -Uadministrator%$ADMIN_PASSWORD

# Remove the Caddy entry
python3 ../remove_caddy_service.py desktop.$DOMAIN
systemctl reload caddy

ufw delete allow from 192.168.0.0/16 to any port 3389
ufw delete allow from 172.16.0.0/12 to any port 3389

# Remove all the users beginning with lw.
USERS=$(ls /home | grep lw.)
for USER in $USERS; do
    deluser $USER
    rm -rf /home/$USER
done


# Remove the OIDC client
# TODO