# The path of the destination is stored in file "export_data"
DESTINATION=`cat ./export_data`

touch export_running

# Dump all databases
mysqldump -u root --all-databases --default-character-set=utf8mb4 > /mysql_all_databases.sql    

# Disable all services
bash ./stop_services.sh

echo "Starting export to $DESTINATION..."

# Copy all files with rsync
rsync -a --delete / $DESTINATION --exclude /dev --exclude /proc --exclude /sys --exclude /tmp --exclude /run --exclude /media --exclude /mnt --exclude /var/log > /var/lib/libre-workspace/portal/history/rsync.log

# Enable all services
bash ./start_services.sh

rm export_running
rm export_data

echo "Export finished!"