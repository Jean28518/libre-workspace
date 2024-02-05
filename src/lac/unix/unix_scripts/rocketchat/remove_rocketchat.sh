#!/bin/bash
docker-compose -f /root/rocket.chat/docker-compose.yml down --volumes
rm -rf /root/rocket.chat
# Remove the entry from the Caddyfile
sed -i "/chat.$DOMAIN {/,/}/d" /etc/caddy/Caddyfile
systemctl restart caddy
