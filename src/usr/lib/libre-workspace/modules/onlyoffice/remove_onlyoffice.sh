# Removes also all data!
# Needs the following variables:
# DOMAIN

libre-workspace-remove-webserver-entry office.$DOMAIN

# If nextcloud is installed, remove the onlyoffice app
if [ -d "/var/www/nextcloud" ]; then
    sudo -u www-data php /var/www/nextcloud/occ app:disable onlyoffice
    sudo -u www-data php /var/www/nextcloud/occ app:remove onlyoffice
fi

# Remove the onlyoffice container
docker rm -f onlyoffice 

# Remove the onlyoffice installation directory
rm -r /root/onlyoffice