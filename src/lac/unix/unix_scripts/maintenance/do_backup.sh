#!/bin/bash
source ../unix.conf

touch backup_running

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
# If $REMOTEPATH is set, then use this command:
if [ -z "$REMOTEPATH" ] ; then
  borg create --exclude-caches $BORG_REPOSITORY::$DATE / -e /dev -e /proc -e /sys -e /tmp -e /run -e /media -e /mnt -e /var/log -e /var/lib/mysql/ib_logfile0 2> ../history/borg_errors_$DATE.log
else
  borg create --remote-path $REMOTEPATH --exclude-caches $BORG_REPOSITORY::$DATE / -e /dev -e /proc -e /sys -e /tmp -e /run -e /media -e /mnt -e /var/log -e /var/lib/mysql/ib_logfile0 2> ../history/borg_errors_$DATE.log
fi

# Start all services
bash ./start_services.sh

borg prune -v $BORG_REPOSITORY \
    --keep-daily=$BORG_KEEP_DAILY \
    --keep-weekly=$BORG_KEEP_WEEKLY \
    --keep-monthly=$BORG_KEEP_MONTHLY \


borg list --short $BORG_REPOSITORY > ../history/borg_list
borg info $BORG_REPOSITORY > ../history/borg_info

rm backup_running