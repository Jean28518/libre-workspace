source /etc/libre-workspace/libre-workspace.conf

mkdir -p /backups

# If encrypted == true, then use this command:
if [ $BORG_ENCRYPTION = true ] ; then
  export BORG_PASSPHRASE=$BORG_PASSPHRASE
else
  export BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
fi

if [ -z "$REMOTEPATH" ] ; then
  borg mount $BORG_REPOSITORY /backups
else
  borg mount --remote-path $REMOTEPATH $BORG_REPOSITORY /backups
fi