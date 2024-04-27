#!/bin/bash
source ../unix.conf

# Dump all databases
# --default-character-set=utf8mb4: For emojis and similar, otherwise its broken 
mysqldump -u root --all-databases --default-character-set=utf8mb4 > /mysql_all_databases.sql    
# To restore a Single MySQL Database from a Full MySQL Dump:
# mysql -p -o database_name < mysql_all_databases.sql

# Get apt selection of packages:
/usr/bin/dpkg --get-selections | /usr/bin/awk '!/deinstall|purge|hold/'|/usr/bin/cut -f1 |/usr/bin/tr '\n' ' '  > /installed-packages.txt  2>&1
# To restore apt packages:
# sudo apt update && sudo xargs apt install </root/installed-packages.txt

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
  borg create --exclude-caches $BORG_REPOSITORY::$DATE-system / -e /dev -e /proc -e /sys -e /tmp -e /run -e /media -e /mnt -e /var/log -e /var/lib/mysql/ib_logfile0 -e /data 2> ../history/borg_errors_$DATE.log
else
  borg create --remote-path $REMOTEPATH --exclude-caches $BORG_REPOSITORY::$DATE-system / -e /dev -e /proc -e /sys -e /tmp -e /run -e /media -e /mnt -e /var/log -e /var/lib/mysql/ib_logfile0 -e /data 2> ../history/borg_errors_$DATE.log
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
    borg create --exclude-caches $BORG_REPOSITORY::$DATE-data /data 2>> ../history/borg_errors_$DATE.log
  else
    borg create --remote-path $REMOTEPATH --exclude-caches $BORG_REPOSITORY::$DATE-data /data 2>> ../history/borg_errors_$DATE.log
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


borg list --short $BORG_REPOSITORY > ../history/borg_list
borg info $BORG_REPOSITORY > ../history/borg_info