DATE=`date +"%Y-%m-%d"`
echo "Starting update at $DATE" >> ../history/update-$DATE.log
echo "Hint: This script runs every day wether some update procedure is enabled or not. If you see 'Cleaning up the system' in the next line, then nothing was updated." >> ../history/update-$DATE.log

. ../unix.conf

if [ "$SYSTEM_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting system update at $DATE" >> ../history/update-$DATE.log 2>&1
    # Get the update log also to our log file
    cat history/update.log >> ../history/update-$DATE.log
    bash do_update.sh >> ../history/update-$DATE.log 2>&1
fi

if [ "$NEXTCLOUD_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting nextcloud update at $DATE" >> ../history/update-$DATE.log 2>&1
    bash ../nextcloud/update_nextcloud.sh >> ../history/update-$DATE.log 2>&1
fi

if [ "$ONLYOFFICE_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting onlyoffice update at $DATE" >> ../history/update-$DATE.log 2>&1
    bash ../onlyoffice/update_onlyoffice.sh >> ../history/update-$DATE.log 2>&1
fi

if [ "$COLLABORA_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting collabora update at $DATE" >> ../history/update-$DATE.log 2>&1
    bash ../collabora/update_collabora.sh >> ../history/update-$DATE.log 2>&1
fi

if [ "$MATRIX_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting matrix update at $DATE" >> ../history/update-$DATE.log 2>&1
    bash ../matrix/update_matrix.sh >> ../history/update-$DATE.log 2>&1
fi

if [ "$JITSI_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting jitsi update at $DATE" >> ../history/update-$DATE.log 2>&1
    bash ../jitsi/update_jitsi.sh >> ../history/update-$DATE.log 2>&1
fi

# Update all addons which are located in /usr/share/linux-arbeitsplatz/unix/unix_scripts/addons
for ADDON in /usr/share/linux-arbeitsplatz/unix/unix_scripts/addons/*; do
    if [ -d "$ADDON" ]; then
        # Get folder name from path.
        ADDON_NAME=$(basename $ADDON)
        # Capitalize the addon name and replace "-" with "_" (because of the variable names in unix.conf)
        ADDON_VAR_NAME=$(echo $ADDON_NAME | sed -e 's/\(.*\)/\U\1/' -e 's/-/_/g')
        if [ "$(eval "echo \$${ADDON_VAR_NAME}_AUTOMATIC_UPDATES")" == "True" ]; then
            echo "Starting update of $ADDON_NAME at $DATE" >> ../history/update-$DATE.log 2>&1
            bash ../addons/$ADDON_NAME/update_$ADDON_NAME.sh >> ../history/update-$DATE.log 2>&1
        fi
    fi
done

echo "Cleaning up system..." >> ../history/update-$DATE.log
bash cleanup.sh >> ../history/update-$DATE.log

if [ "$LIBRE_WORKSPACE_AUTOMATIC_UPDATES" == "True" ]; then
    echo "Starting libre workspace update at $DATE" >> ../history/update-$DATE.log 2>&1
    # Get the update log also to our log file
    cd /usr/share/linux-arbeitsplatz/
    bash ./update_libre_workspace.sh >> ../history/update-$DATE.log 2>&1
    cd /usr/share/linux-arbeitsplatz/unix/unix_scripts/maintenance
fi