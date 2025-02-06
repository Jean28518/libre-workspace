systemctl start mariadb
systemctl start docker

# Turn on maintenance mode of Nextcloud
if [ -f /var/www/nextcloud/occ ]; then
    sudo -u www-data /usr/bin/php /var/www/nextcloud/occ maintenance:mode --off
fi

# If file start_additional_services.sh exists, run it
if [ -f ./start_additional_services.sh ]; then
    bash ./start_additional_services.sh
fi
