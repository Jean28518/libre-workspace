# This script recovers a file or directory from the backup and copies it to the original location
# The backup has to be mounted before running this script

# The path to recover is in the first argument
RECOVER_PATH=$1
# Ensure that path ends not with a slash
RECOVER_PATH=${RECOVER_PATH%/}

# The path where we want to copy the recovered file(s) can be dereived also from the first argument
# The first argument has the path /backups/YYYY-MM-DD/
# Remove /backups/YYYY-MM-DD/ from the path and use the rest as the destination path
DESTINATION_PATH=${RECOVER_PATH#/backups/*/}
DESTINATION_PATH=/$DESTINATION_PATH
# DESTINATION_PATH is now /path/to/recover/
# Remove the last folder from the path
DESTINATION_PATH=${DESTINATION_PATH%/*}

# If we are now at the root of the filesystem, then we have to add a slash to the path
if [ -z "$DESTINATION_PATH" ]; then
    DESTINATION_PATH=/
fi


touch recovering_in_progress
PARENT_DIR=$(dirname $DESTINATION_PATH)
mkdir -p $PARENT_DIR
cp -ra $RECOVER_PATH $DESTINATION_PATH

if [ $? -ne 0 ]; then
    echo "Failed to recover $RECOVER_PATH to $DESTINATION_PATH"
    rm recovering_in_progress
    exit 1
fi

echo "Recovered $RECOVER_PATH to $DESTINATION_PATH"

# If the path has "nextcloud" in it, then we have to rescan the files
if [[ $RECOVER_PATH == *"nextcloud"* ]]; then
    sudo -u www-data php /var/www/nextcloud/occ files:scan --all
fi
rm recovering_in_progress