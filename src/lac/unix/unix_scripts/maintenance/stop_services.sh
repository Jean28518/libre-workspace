. umount_backups.sh

# Turn off maintenance mode of Nextcloud
if [ -f /var/www/nextcloud/occ ]; then
    sudo -u www-data /usr/bin/php /var/www/nextcloud/occ maintenance:mode --on
fi

systemctl stop docker
systemctl stop mariadb

# If file stop_additional_services.sh exists, run it
if [ -f ./stop_additional_services.sh ]; then
    bash ./stop_additional_services.sh
fi
