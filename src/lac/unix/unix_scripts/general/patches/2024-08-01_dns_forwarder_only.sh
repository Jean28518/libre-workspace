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
# Check if "dns forwarder resolve only" is set in /etc/samba/smb.conf. If yes, then we need to exit the patch
if grep -q "dns forwarder resolve only" /etc/samba/smb.conf; then
  echo "dns forwarder resolve only is already set. Exiting patch."
  exit 0
fi

# Set "dns forwarder resolve only" in /etc/samba/smb.conf
echo "" >> /etc/samba/smb.conf
echo "# Only resolve DNS requests via the forwarder" >> /etc/samba/smb.conf
echo "dns forwarder resolve only = yes" >> /etc/samba/smb.conf