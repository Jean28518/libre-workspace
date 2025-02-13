#!/bin/bash
# This script gets these variables passed: $DOMAIN, $ADMIN_PASSWORD, $IP, $LDAP_DC
mkdir -p /root/{{addon.id}}
# Dont forget to escape " with a backslash:
cp docker-compose.yml /root/{{addon.id}}/docker-compose.yml

docker-compose -f /root/{{addon.id}}/docker-compose.yml up -d

echo "{{addon.url}}.$DOMAIN {
    #tls internal
    reverse_proxy localhost:{{addon.internal_port}}
}

" >> /etc/caddy/Caddyfile

# If domain is "int.de" uncomment the tls internal line for internal https
if [ "$DOMAIN" = "int.de" ]; then
    sed -i 's/#tls internal/tls internal/g' /etc/caddy/Caddyfile
fi

systemctl reload caddy