#!/bin/bash

# Check for additional key then we read these variables with the additional id
if [ ! -z $1 ] ; then
  cat /etc/libre-workspace/libre-workspace.conf | grep _$1 > /tmp/libre-workspace.conf
  sed -i "s/_$1//g" /tmp/libre-workspace.conf
  source /tmp/libre-workspace.conf
  rm /tmp/libre-workspace.conf
  BACKUP_FOLDER=/backups_$1/
else
  source /etc/libre-workspace/libre-workspace.conf
  BACKUP_FOLDER=/backups
fi

echo $1
echo "Mounting backups to $BACKUP_FOLDER"

mkdir -p $BACKUP_FOLDER

# If encrypted == true, then use this command:
if [ $BORG_ENCRYPTION = true ] ; then
  export BORG_PASSPHRASE=$BORG_PASSPHRASE
else
  export BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
fi

if [ -z "$REMOTEPATH" ] ; then
  borg mount $BORG_REPOSITORY $BACKUP_FOLDER
else
  borg mount --remote-path $REMOTEPATH $BORG_REPOSITORY $BACKUP_FOLDER
fi