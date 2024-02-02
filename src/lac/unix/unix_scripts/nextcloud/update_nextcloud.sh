sudo -u www-data php /var/www/nextcloud/updater/updater.phar --no-interaction
sudo -u www-data php /var/www/nextcloud/occ upgrade

# Update the database
sudo -u www-data php /var/www/nextcloud/occ db:add-missing-indices