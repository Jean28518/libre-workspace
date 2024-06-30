#!/bin/bash
source ../unix.conf

touch update_running

CURRENT_TIME=`date +"%Y-%m-%d_%H-%M-%S"`

echo "$CURRENT_TIME: Starting update..." > ../history/update.log

apt-get update >> ../history/update.log

DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y >> ../history/update.log

rm update_running