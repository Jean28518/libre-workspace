systemctl stop docker
. umount_backups.sh

# Turn off maintenance mode of Nextcloud
if [ -f /var/www/nextcloud/occ ]; then
    sudo -u www-data /usr/bin/php /var/www/nextcloud/occ maintenance:mode --on
fi