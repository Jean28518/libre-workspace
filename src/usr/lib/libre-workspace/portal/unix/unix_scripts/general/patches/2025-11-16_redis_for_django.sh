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


# Check if we need to apply the patch
# Do we find "requirepass" in /etc/redis/redis.conf?
if grep -q "requirepass" /etc/redis/redis.conf; then
  # Check if REDIS_PASSWORD is set in /etc/libre-workspace/portal/portal.conf
  if grep -q "REDIS_PASSWORD" /etc/libre-workspace/portal/portal.conf; then
    REDIS_PASSWORD_VALUE=$(grep "REDIS_PASSWORD" /etc/libre-workspace/portal/portal.conf)
    if [ ! -z "$REDIS_PASSWORD_VALUE" ] ; then
      echo "Redis already configured with password. Exiting patch."
      exit 0
    fi
  exit 0
fi

# BEGIN APPLYING PATCH
apt install redis -y


# Check if already requirepass is set, then we dont need to set it again
REDIS_PASSWORD=$(grep "requirepass" /etc/redis/redis.conf | awk '{print $2}')
if [ -z "$REDIS_PASSWORD" ] ; then
  REDIS_PASSWORD=$(libre-workspace-generate-secret 32)
  echo "" >> /etc/redis/redis.conf
  echo "requirepass $REDIS_PASSWORD" >> /etc/redis/redis.conf
fi

# Remove all REDIS_PASSWORD lines from /etc/libre-workspace/portal/portal.conf
sed -i '/REDIS_PASSWORD/d' /etc/libre-workspace/portal/portal.conf
# Add REDIS_PASSWORD to /etc/libre-workspace/portal/portal.conf
echo "
export REDIS_PASSWORD=\"$REDIS_PASSWORD\"" >> /etc/libre-workspace/portal/portal.conf

systemctl enable redis-server
systemctl restart redis-server
systemctl restart libre-workspace-portal.service
