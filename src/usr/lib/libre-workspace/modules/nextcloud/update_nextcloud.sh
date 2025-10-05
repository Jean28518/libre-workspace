sudo -u www-data php /var/www/nextcloud/updater/updater.phar --no-interaction
sudo -u www-data php /var/www/nextcloud/occ upgrade

# Update the database
sudo -u www-data php /var/www/nextcloud/occ db:add-missing-indices

# Repair nextcloud (sometimes this is needed by nextcloud itself.)
sudo -u www-data php /var/www/nextcloud/occ maintenance:repair --include-expensive

# In case the oidc app gets disabled: re-enable it
sudo -u www-data php /var/www/nextcloud/occ app:install oidc_login --force
sudo -u www-data php /var/www/nextcloud/occ app:enable oidc_login --force
# Restart php-fpm and redis to make sure everything is fresh (oidc_login needs those restarts)
systemctl restart redis.service php*fpm.service