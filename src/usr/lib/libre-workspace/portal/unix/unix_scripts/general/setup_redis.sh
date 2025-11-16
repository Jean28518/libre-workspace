#!/bin/bash

apt install redis -y
REDIS_PASSWORD=$(libre-workspace-generate-secret 32)
libre-workspace-config-tool --file-type space set /etc/redis/redis.conf requirepass "$REDIS_PASSWORD"

systemctl enable redis-server
systemctl restart redis-server

libre-workspace-config-tool --file-type rc set /etc/libre-workspace/portal/portal.conf REDIS_ADDRESS "redis://:$REDIS_PASSWORD@127.0.0.1:6379/1" 