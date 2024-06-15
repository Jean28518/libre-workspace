# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP

mkdir -p /root/onlyoffice


echo "docker pull onlyoffice/documentserver:latest
docker run -i -t -d -p 10923:80 --restart=unless-stopped --name onlyoffice -e JWT_ENABLED='true' -e JWT_SECRET='$ADMIN_PASSWORD' --add-host \"cloud.$DOMAIN:$IP\" onlyoffice/documentserver:latest" > /root/onlyoffice/run.sh


if [ "$DOMAIN" = "int.de" ] ; then
  echo "
docker exec onlyoffice sed -i 's/\"rejectUnauthorized\": true/\"rejectUnauthorized\": false/g' /etc/onlyoffice/documentserver/default.json
docker restart onlyoffice
" >> /root/onlyoffice/run.sh
fi

bash /root/onlyoffice/run.sh

# Add the content of caddy_onlyoffice_entry.txt to /etc/caddy/Caddyfile
cat caddy_onlyoffice_entry.txt >> /etc/caddy/Caddyfile
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile


# if $DOMAIN = "int.de" then uncomment #tls internal
if [ "$DOMAIN" = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
fi

systemctl restart caddy



# Install in nextcloud the onlyoffice app
sudo -u www-data php /var/www/nextcloud/occ app:install onlyoffice
# We need this because if we removed it before and then reinstalled it, it is disabled:
sudo -u www-data php /var/www/nextcloud/occ app:enable onlyoffice

# Configure onlyoffice
sudo -u www-data php /var/www/nextcloud/occ config:app:set onlyoffice DocumentServerUrl --value="https://office.$DOMAIN/"
# Set the secret ($ADMIN_PASSWORD)
sudo -u www-data php /var/www/nextcloud/occ config:app:set onlyoffice jwt_secret --value="$ADMIN_PASSWORD"
# if $DOMAIN = "int.de" then deactivate the certificate verification
if [ "$DOMAIN" = "int.de" ] ; then
  sudo -u www-data php /var/www/nextcloud/occ config:app:set onlyoffice verify_peer_off --value="true"
fi
# Disable the document preview
sudo -u www-data php /var/www/nextcloud/occ config:app:set onlyoffice preview --value="false"