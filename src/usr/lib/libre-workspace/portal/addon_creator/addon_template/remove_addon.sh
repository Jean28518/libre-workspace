#!/bin/bash
# This script gets these variables passed: $DOMAIN, $ADMIN_PASSWORD, $IP, $LDAP_DC

docker-compose -f /root/{{addon.id}}/docker-compose.yml down --volumes
rm -rf /root/{{addon.id}}
# Remove the entry from the Caddyfile
libre-workspace-remove-webserver-entry {{addon.url}}.$DOMAIN
systemctl restart caddy