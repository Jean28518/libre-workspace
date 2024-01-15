DATE=`date +"%Y-%m-%d"`
echo "Starting update at $DATE" >> ./history/update-$DATE.log
echo "Hint: This script runs every day wether some update procedure is enabled or not. If you see 'Cleaning up the system' in the next line, then nothing was updated." >> ./history/update-$DATE.log

. unix.conf

if [ "$SYSTEM_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting system update at $DATE" >> ./history/update-$DATE.log
    # Get the update log also to our log file
    cat history/update.log >> ./history/update-$DATE.log
    bash do_update.sh >> ./history/update-$DATE.log
fi

if [ "$NEXTCLOUD_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting nextcloud update at $DATE" >> ./history/update-$DATE.log
    bash nextcloud/update_nextcloud.sh >> ./history/update-$DATE.log
fi

if [ "$ONLYOFFICE_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting onlyoffice update at $DATE" >> ./history/update-$DATE.log
    bash onlyoffice/update_onlyoffice.sh >> ./history/update-$DATE.log
fi

if [ "$COLLABORA_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting collabora update at $DATE" >> ./history/update-$DATE.log
    bash collabora/update_collabora.sh >> ./history/update-$DATE.log
fi

if [ "$ROCKETCHAT_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting rocketchat update at $DATE" >> ./history/update-$DATE.log
    bash rocketchat/update_rocketchat.sh >> ./history/update-$DATE.log
fi

if [ "$JITSI_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting jitsi update at $DATE" >> ./history/update-$DATE.log
    bash jitsi/update_jitsi.sh >> ./history/update-$DATE.log
fi

echo "Cleaning up system..." >> ./history/update-$DATE.log
bash cleanup.sh >> ./history/update-$DATE.log