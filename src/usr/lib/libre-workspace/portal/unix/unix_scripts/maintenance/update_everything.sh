DATE=`date +"%Y-%m-%d"`
echo "Starting update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log
echo "Hint: This script runs every day wether some update procedure is enabled or not. If you see 'Cleaning up the system' in the next line, then nothing was updated." >> /var/lib/libre-workspace/portal/history/update-$DATE.log

. /etc/libre-workspace/libre-workspace.conf

if [ "$SYSTEM_AUTOMATIC_UPDATES" == "True" | "$SYSTEM_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting system update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash do_update.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    # Because do_update.sh has its own log file, we append it to our log file
    cat /var/lib/libre-workspace/portal/history/update.log >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

if [ "$NEXTCLOUD_AUTOMATIC_UPDATES" == "True" | "$NEXTCLOUD_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting nextcloud update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash /usr/lib/libre-workspace/modules/nextcloud/update_nextcloud.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

if [ "$DESKTOP_AUTOMATIC_UPDATES" == "True" | "$DESKTOP_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting cloud desktop update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash /usr/lib/libre-workspace/modules/desktop/update_desktop.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

if [ "$ONLYOFFICE_AUTOMATIC_UPDATES" == "True" | "$ONLYOFFICE_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting onlyoffice update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash /usr/lib/libre-workspace/modules/onlyoffice/update_onlyoffice.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

if [ "$COLLABORA_AUTOMATIC_UPDATES" == "True" | "$COLLABORA_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting collabora update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash /usr/lib/libre-workspace/modules/collabora/update_collabora.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

if [ "$MATRIX_AUTOMATIC_UPDATES" == "True" | "$MATRIX_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting matrix update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash /usr/lib/libre-workspace/modules/matrix/update_matrix.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

if [ "$JITSI_AUTOMATIC_UPDATES" == "True" | "$JITSI_AUTOMATIC_UPDATES" == "" ]; then
    echo "Starting jitsi update at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
    bash /usr/lib/libre-workspace/modules/jitsi/update_jitsi.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
fi

# Update all addons which are located in /usr/lib/libre-workspace/modules
for ADDON in /usr/lib/libre-workspace/modules/*; do
    if [ -d "$ADDON" ]; then
        # Get folder name from path.
        ADDON_NAME=$(basename $ADDON)
        # Capitalize the addon name and replace "-" with "_" (because of the variable names in /etc/libre-workspace/libre-workspace.conf)
        ADDON_VAR_NAME=$(echo $ADDON_NAME | sed -e 's/\(.*\)/\U\1/' -e 's/-/_/g')
        if [ "$(eval "echo \$${ADDON_VAR_NAME}_AUTOMATIC_UPDATES")" == "True" | "$(eval "echo \$${ADDON_VAR_NAME}_AUTOMATIC_UPDATES")" == "" ]; then
            echo "Starting update of $ADDON_NAME at $DATE" >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
            bash /usr/lib/libre-workspace/modules/$ADDON_NAME/update_$ADDON_NAME.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log 2>&1
        fi
    fi
done

echo "Cleaning up system..." >> /var/lib/libre-workspace/portal/history/update-$DATE.log
bash cleanup.sh >> /var/lib/libre-workspace/portal/history/update-$DATE.log