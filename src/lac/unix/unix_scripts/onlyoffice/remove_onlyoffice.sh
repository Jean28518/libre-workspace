# Removes also all data!
# Needs the following variables:
# DOMAIN

python3 /usr/share/linux-arbeitsplatz/unix/unix_scripts/remove_caddy_service.py office.$DOMAIN

# If nextcloud is installed, remove the onlyoffice app
if [ -d "/var/www/nextcloud" ]; then
    sudo -u www-data php /var/www/nextcloud/occ app:disable onlyoffice
fi

# Remove the onlyoffice container
docker rm -f onlyoffice 

# Remove the onlyoffice installation directory
rm -r /root/onlyoffice