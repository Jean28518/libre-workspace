#!/bin/bash

apt install redis -y
REDIS_PASSWORD=$(libre-workspace-generate-secret 32)
libre-workspace-config-tool --file-type space set /etc/redis/redis.conf requirepass "$REDIS_PASSWORD"

systemctl enable redis-server
systemctl restart redis-server

libre-workspace-config-tool --file-type space set /etc/libre-workspace/portal/portal.conf REDIS_PASSWORD "$REDIS_PASSWORD" 