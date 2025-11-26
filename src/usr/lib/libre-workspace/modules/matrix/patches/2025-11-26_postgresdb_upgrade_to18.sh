#!/bin/bash

# IS THIS PATCH OLDER THAN 365 DAYS?
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
# Is "image: postgres:13" in the docker-compose.yml file?
if [ $(grep -c "image: postgres:13" /root/matrix/docker-compose.yml) -eq 0 ]; then
  echo "Patch already applied. Exiting patch."
  exit 0
fi

# BEGIN APPLYING PATCH
cd /root/matrix
docker exec -it matrix-db-1 pg_dumpall -U synapse > ./upgrade_backup.sql
docker compose down
mv postgres-data postgres-data.old
# Change version from postgres 13 to 18 in docker compose yml
sed -i 's/image: postgres:13/image: postgres:18/' docker-compose.yml
# Change the mount to   /var/lib/postgresql
sed -i 's|      - ./postgres-data:/var/lib/postgresql/data|      - ./postgres-data:/var/lib/postgresql|' docker-compose.yml

docker compose up -d db
sleep 10
cat ./upgrade_backup.sql | docker exec -i matrix-db-1 psql -U synapse -d synapse
docker exec matrix-db-1 psql -U synapse -d synapse -c "ALTER USER synapse WITH PASSWORD 'OoRei7oh';"
docker compose up -d

sleep 10

# Make sure element config is updated
. /etc/libre-workspace/libre-workspace.env
. /usr/lib/libre-workspace/modules/matrix/update_element_config.sh