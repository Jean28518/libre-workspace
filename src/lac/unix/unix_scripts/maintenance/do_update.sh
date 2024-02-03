#!/bin/bash
source ../unix.conf

touch update_running

# Stop all services
bash ./stop_services.sh

CURRENT_TIME=`date +"%Y-%m-%d_%H-%M-%S"`

echo "$CURRENT_TIME: Starting update..." > ../history/update.log

apt update >> ../history/update.log

DEBIAN_FRONTEND=noninteractive apt dist-upgrade -y >> ../history/update.log

# Start all services
bash ./start_services.sh

rm update_running