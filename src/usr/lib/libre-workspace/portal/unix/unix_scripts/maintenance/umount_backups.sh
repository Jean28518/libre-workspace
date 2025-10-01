
# Check for additional key then we read these variables with the additional id
if [ ! -z $1] ; then
  borg umount /backups_$1/
else
  borg umount /backups
fi

