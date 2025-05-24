# Removes also all data!
# Needs the following variables:
# DOMAIN

python3 ../remove_caddy_service.py cloud.$DOMAIN

if [ -d "/data/nextcloud" ]; then
  rm -r /data/nextcloud
fi

# Drop the nextcloud database
mysql -u root -p -e "DROP DATABASE nextcloud;"

# Remove the cronjob
crontab -u www-data -l | grep -v "/var/www/nextcloud/cron.php"  | crontab -u www-data -

# Remove the nextcloud installation directory
rm -r /var/www/nextcloud