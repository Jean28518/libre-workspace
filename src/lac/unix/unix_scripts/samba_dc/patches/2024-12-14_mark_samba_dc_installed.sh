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
# Is samba installed and not /root/samba_dc exists?
if [ -x "$(command -v samba-tool)" ] && [ -f /root/samba_dc ]; then
  echo "Samba is already installed and marked. Exiting patch."
  exit 0
fi

# Mark samba_dc installed if samba-tool is installed
if [ -x "$(command -v samba-tool)" ]; then
  ln -s /etc/samba /root/samba_dc
fi