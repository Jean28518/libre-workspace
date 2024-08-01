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
# Is localhost not in the trusted domains? Then we need to exit the patch
if ! sudo -u www-data php /var/www/nextcloud/occ config:system:get trusted_domains | grep -q localhost; then
  if ! sudo -u www-data php /var/www/nextcloud/occ config:system:get overwrite.cli.url | grep -q localhost; then
    echo "Localhost is not in the trusted domains and not in overwrite.cli.url Everything okay. Exiting patch."
    exit 0
  fi
fi

sudo -u www-data php /var/www/nextcloud/occ config:system:delete trusted_domains 0
sudo -u www-data php /var/www/nextcloud/occ config:system:set trusted_domains 0 --value cloud.$DOMAIN
sudo -u www-data php /var/www/nextcloud/occ config:system:set overwrite.cli.url --value https://cloud.$DOMAIN