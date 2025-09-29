#!/bin/bash

# Check for additional key then we read these variables with the additional id
if [ ! -z $1] ; then
  cat /etc/libre-workspace/libre-workspace.conf | grep _$1 > /tmp/libre-workspace.conf
  sed -i "s/_$1//g" /tmp/libre-workspace.conf
  source /tmp/libre-workspace.conf
  rm /tmp/libre-workspace.conf
  HISTORY_FOLDER=/var/lib/libre-workspace/portal/additional_backup_$1/
else
  source /etc/libre-workspace/libre-workspace.conf
  HISTORY_FOLDER=/var/lib/libre-workspace/portal/history/
fi



# Dump all databases
# --default-character-set=utf8mb4: For emojis and similar, otherwise its broken 
mysqldump -u root --all-databases --default-character-set=utf8mb4 --lock-all-tables > /mysql_all_databases.sql    
# To restore a Single MySQL Database from a Full MySQL Dump:
# mysql -p -o database_name < mysql_all_databases.sql
# Otherwise e.g.:
# mysql -u nextcloud -p nextcloud
# MariaDB [nextcloud]> source mysql_export.sql

# Get apt selection of packages:
/usr/bin/dpkg --get-selections | /usr/bin/awk '!/deinstall|purge|hold/'|/usr/bin/cut -f1 |/usr/bin/tr '\n' ' '  > /var/lib/libre-workspace/portal/installed-packages.txt  2>&1
# To restore apt packages:
# sudo apt update && sudo xargs apt install </var/lib/libre-workspace/portal/installed-packages.txt

# Stop all services
bash ./stop_services.sh

DATE=`date +"%Y-%m-%d"`

# If encrypted == true, then use this command:
if [ $BORG_ENCRYPTION = true ] ; then
  export BORG_PASSPHRASE=$BORG_PASSPHRASE
else
  export BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
fi


# If $REMOTEPATH is set, then use this command:
if [ -z "$REMOTEPATH" ] ; then
  borg create --exclude-caches $BORG_REPOSITORY::$DATE-system / -e /dev -e /proc -e /sys -e /tmp -e /run -e /media -e /mnt -e /var/log -e /data $ADDITIONAL_BORG_OPTIONS 2> $HISTORY_FOLDER/borg_errors_$DATE.log
else
  borg create --remote-path $REMOTEPATH --exclude-caches $BORG_REPOSITORY::$DATE-system / -e /dev -e /proc -e /sys -e /tmp -e /run -e /media -e /mnt -e /var/log -e /data $ADDITIONAL_BORG_OPTIONS 2> $HISTORY_FOLDER/borg_errors_$DATE.log
fi

# Start all services
bash ./start_services.sh

# Prune old system backups
borg prune -v --glob-archives '*-system' $BORG_REPOSITORY \
    --keep-daily=$BORG_KEEP_DAILY \
    --keep-weekly=$BORG_KEEP_WEEKLY \
    --keep-monthly=$BORG_KEEP_MONTHLY



# Then backup the /data directory while the services are running, because it is a big directory and takes a long time to backup
# Also there are no databases in /data, so it is not a problem to backup it after the critical services
if [ -d /data ]; then
  if [ -z "$REMOTEPATH" ] ; then
    borg create --exclude-caches $BORG_REPOSITORY::$DATE-data /data $ADDITIONAL_BORG_OPTIONS 2>> $HISTORY_FOLDER/borg_errors_$DATE.log
  else
    borg create --remote-path $REMOTEPATH --exclude-caches $BORG_REPOSITORY::$DATE-data /data $ADDITIONAL_BORG_OPTIONS 2>> $HISTORY_FOLDER/borg_errors_$DATE.log
  fi
  # BORG_KEEP_DAILY=$((2*$BORG_KEEP_DAILY))
  # BORG_KEEP_WEEKLY=$((2*$BORG_KEEP_WEEKLY))
  # BORG_KEEP_MONTHLY=$((2*$BORG_KEEP_MONTHLY))
  # Prune old backups
  borg prune -v --glob-archives '*-data' $BORG_REPOSITORY \
    --keep-daily=$BORG_KEEP_DAILY \
    --keep-weekly=$BORG_KEEP_WEEKLY \
    --keep-monthly=$BORG_KEEP_MONTHLY
fi

# # Delete old backups which are older than $MAXIMUM_AGE_IN_DAYS and are falling through the regular pruning e.g. because of other naming
MAXIMUM_AGE_IN_DAYS=$((31*$BORG_KEEP_MONTHLY))d
borg prune -v --keep-within=$MAXIMUM_AGE_IN_DAYS $BORG_REPOSITORY


borg list --short $BORG_REPOSITORY > $HISTORY_FOLDER/borg_list

if [ -z "$REMOTEPATH" ] ; then
  borg info $BORG_REPOSITORY > $HISTORY_FOLDER/borg_info
else
  borg info --remote-path $REMOTEPATH $BORG_REPOSITORY > $HISTORY_FOLDER/borg_info
fi
