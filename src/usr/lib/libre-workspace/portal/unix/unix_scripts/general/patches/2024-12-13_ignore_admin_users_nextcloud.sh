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
# Check if "IGNORE_ADMIN_STATUS_FOR_NEXTCLOUD_USERS" is in /etc/libre-workspace/portal/portal.conf
# If this is set then exit the patch
if grep -q "IGNORE_ADMIN_STATUS_FOR_NEXTCLOUD_USERS" /etc/libre-workspace/portal/portal.conf; then
  echo "IGNORE_ADMIN_STATUS_FOR_NEXTCLOUD_USERS is set in /etc/libre-workspace/portal/portal.conf. Exiting patch."
  exit 0
fi

# Add "IGNORE_ADMIN_STATUS_FOR_NEXTCLOUD_USERS" to /etc/libre-workspace/portal/portal.conf
echo "
# Don't change the admin status for these nextcloud users automatically also if they are not in group "Domain Admin". Separate them with ,
export IGNORE_ADMIN_STATUS_FOR_NEXTCLOUD_USERS=""
" >> /etc/libre-workspace/portal/portal.conf

systemctl restart libre-workspace-service.service