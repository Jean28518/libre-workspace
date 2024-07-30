#!/bin/bash

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
# Is redis installed?
if [ -x "$(command -v redis-server)" ]; then
  echo "Redis is already installed. Exiting patch."
  exit 0
fi

# Install redis and php packages
apt-get install redis php-redis php-apcu php-memcache pwgen -y

# Set redis password
REDIS_PASSWORD=$(pwgen -n 20 1)
echo "" >> /etc/redis/redis.conf
echo "requirepass $REDIS_PASSWORD" >> /etc/redis/redis.conf

# Enable redis and restart it
systemctl enable redis-server
systemctl restart redis-server

# Configure nextcloud to use redis
# Disable all caches that nextcloud doesn't fail while we are changing the cache settings
sudo -u www-data php /var/www/nextcloud/occ config:system:delete memcache.local
sudo -u www-data php /var/www/nextcloud/occ config:system:delete memcache.distributed
sudo -u www-data php /var/www/nextcloud/occ config:system:delete memcache.locking

sudo -u www-data php /var/www/nextcloud/occ config:system:set redis host --value localhost
sudo -u www-data php /var/www/nextcloud/occ config:system:set redis port --value 6379
sudo -u www-data php /var/www/nextcloud/occ config:system:set redis dbindex --value 0
sudo -u www-data php /var/www/nextcloud/occ config:system:set redis password --value "$REDIS_PASSWORD"
sudo -u www-data php /var/www/nextcloud/occ config:system:set memcache.locking --value '\OC\Memcache\Redis'
sudo -u www-data php /var/www/nextcloud/occ config:system:set memcache.distributed --value '\OC\Memcache\Redis'
# We set the local cache to APCu, because it is faster than redis for local cache
sudo -u www-data php /var/www/nextcloud/occ config:system:set memcache.local --value '\OC\Memcache\APCu'

# Restart php
systemctl restart php*

# If /root/redis-nextcloud/docker-compose.yml exists, then remove it
if [ -f /root/redis-nextcloud/docker-compose.yml ]; then
  docker-compose -f /root/redis-nextcloud/docker-compose.yml down --volumes
  rm -rf /root/redis-nextcloud
fi