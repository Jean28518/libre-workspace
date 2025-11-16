#!/bin/bash

# IS THIS PATCH OLDER THAN 365 DAYS?
# Get the current file name
FILE_NAME=$(basename $0)
# Get the date of the filename which is like this: 2024-06-25
DATE=${FILE_NAME:0:10}
# Check if the file is older than 365 days
if [ $(( ($(date +%s) - $(date -d $DATE +%s)) / 86400 )) -gt 365 ]; then
  echo "Patch is older than 365 days. Exiting patch."
  exit 0
fi

# Check if already requirepass is set, then we dont need to set it again
REDIS_PASSWORD=$(libre-workspace-config-tool --file-type space get /etc/redis/redis.conf requirepass)

# Check if we need to apply the patch
# Do we find "requirepass" in /etc/redis/redis.conf?
if [ ! -z "$REDIS_PASSWORD" ] ; then
  # Check if REDIS_PASSWORD is set in /etc/libre-workspace/portal/portal.conf
  PORTAL_REDIS_PASSWORD=$(libre-workspace-config-tool --file-type rc get /etc/libre-workspace/portal/portal.conf REDIS_PASSWORD)
  if [ ! -z "$PORTAL_REDIS_PASSWORD" ] ; then
    echo "Redis already configured with password in portal.conf. Exiting patch."
    exit 0
  fi
fi

# BEGIN APPLYING PATCH
apt install redis -y


if [ -z "$REDIS_PASSWORD" ] ; then
  REDIS_PASSWORD=$(libre-workspace-generate-secret 32)
  libre-workspace-config-tool --file-type space set /etc/redis/redis.conf requirepass "$REDIS_PASSWORD"
fi

libre-workspace-config-tool --file-type rc set /etc/libre-workspace/portal/portal.conf REDIS_ADDRESS "redis://:$REDIS_PASSWORD@127.0.0.1:6379/1" 

systemctl enable redis-server
systemctl restart redis-server
systemctl restart libre-workspace-portal.service
