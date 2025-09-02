#!/bin/bash
source /etc/libre-workspace/libre-workspace.conf

touch /var/lib/libre-workspace/portal/update_running

CURRENT_TIME=`date +"%Y-%m-%d_%H-%M-%S"`

echo "$CURRENT_TIME: Starting update..." > /var/lib/libre-workspace/portal/history/update.log

apt-get update >> /var/lib/libre-workspace/portal/history/update.log

DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y >> /var/lib/libre-workspace/portal/history/update.log

# Check if we need to update to debian 13
bash /usr/lib/libre-workspace/portal/unix/unix_scripts/general/upgrade_debian.sh


rm /var/lib/libre-workspace/portal/update_running