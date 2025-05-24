#!/bin/bash

# This script removes a user from the linux-server.
# We don't care about the guacamole database because it get's irrelevant after the user is removed.

# This script should be run as root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# As variable we need the username
USERNAME=$1

deluser lw.$USERNAME
rm -rf /home/lw.$USERNAME

# Get the line number of the user in the sshd_config file
LINE_NUMBER=$(grep -n "Match User lw.$USERNAME" /etc/ssh/sshd_config | cut -d: -f1)
# Delete this line and the next line
sed -i "$LINE_NUMBER,+1d" /etc/ssh/sshd_config

systemctl restart sshd
