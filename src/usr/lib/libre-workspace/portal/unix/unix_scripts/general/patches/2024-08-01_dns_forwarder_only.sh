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
# Check if "dns forwarder resolve only" is set in /etc/samba/smb.conf. If not, then exit the patch.
if ! grep -q "dns forwarder resolve only" /etc/samba/smb.conf; then
  echo "dns forwarder resolve only is not set in /etc/samba/smb.conf. Exiting patch."
  exit 0
fi

# Remove "dns forwarder resolve only" from /etc/samba/smb.conf
sed -i '/dns forwarder resolve only/d' /etc/samba/smb.conf

# Update November 2024:
# The "dns forwarder resolve only" option is no longer supported in Samba 4.16 and later.
# So we remove the option from the configuration file to avoid any issues.
