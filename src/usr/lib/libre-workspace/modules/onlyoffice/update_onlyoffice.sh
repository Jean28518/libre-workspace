#!/bin/bash


cd /root/onlyoffice

docker rm -f onlyoffice
bash run.sh

# Update onlyoffice app inside nextcloud
sudo -u www-data php /var/www/nextcloud/occ app:update onlyoffice

# Set the settings_error to "" to prevent onlyoffice from disabling itself
sudo -u www-data php /var/www/nextcloud/occ  config:app:set onlyoffice settings_error --value ""