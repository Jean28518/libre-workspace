. umount_backups.sh

# Turn off maintenance mode of Nextcloud
if [ -f /var/www/nextcloud/occ ]; then
    sudo -u www-data /usr/bin/php /var/www/nextcloud/occ maintenance:mode --on
fi

# Get the current php version
PHP_VERSION=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')

systemctl stop docker
systemctl stop php$PHP_VERSION-fpm
systemctl stop mariadb

# If file stop_additional_services.sh exists, run it
if [ -f /var/lib/libre-workspace/portal/stop_additional_services.sh ]; then
    bash /var/lib/libre-workspace/portal/stop_additional_services.sh
fi
