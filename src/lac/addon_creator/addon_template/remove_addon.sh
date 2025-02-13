#!/bin/bash
# This script gets these variables passed: $DOMAIN, $ADMIN_PASSWORD, $IP, $LDAP_DC

docker-compose -f /root/{{addon.id}}/docker-compose.yml down --volumes
rm -rf /root/{{addon.id}}
# Remove the entry from the Caddyfile
python3 /usr/share/linux-arbeitsplatz/unix/unix_scripts/remove_caddy_service.py {{addon.url}}.$DOMAIN
systemctl reload caddy