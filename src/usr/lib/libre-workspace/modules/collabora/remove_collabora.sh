# Removes also all data!
# Needs the following variables:
# DOMAIN

python3 ../remove_caddy_service.py office.$DOMAIN

# If nextcloud is installed, remove the nextcloud office app
if [ -d "/var/www/nextcloud" ]; then
    sudo -u www-data php /var/www/nextcloud/occ app:disable richdocuments
fi

# Remove the collabora container
docker rm -f collabora 

# Remove the collabora installation directory
rm -r /root/collabora