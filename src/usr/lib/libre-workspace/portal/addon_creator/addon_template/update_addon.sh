#!/bin/bash
# This script gets these variables passed: $DOMAIN, $ADMIN_PASSWORD, $IP, $LDAP_DC

docker compose -f /root/{{addon.id}}/docker-compose.yml pull
docker compose -f /root/{{addon.id}}/docker-compose.yml up -d