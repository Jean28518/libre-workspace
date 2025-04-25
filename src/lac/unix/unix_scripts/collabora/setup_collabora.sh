# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP

SCND_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f1`
FRST_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f2`

mkdir -p /root/collabora


echo "docker pull collabora/code:latest
docker run -t -d -p 9980:9980 -e "aliasgroup1=https://cloud\\\\.$SCND_DOMAIN_LABEL\\\\.$FRST_DOMAIN_LABEL:443" -e "username=admin" -e "password=beiSee8e" --restart unless-stopped --name collabora --add-host cloud.$DOMAIN:$IP collabora/code:latest" > /root/collabora/run.sh

bash /root/collabora/run.sh
docker exec collabora echo "$IP cloud.$DOMAIN" >> /etc/hosts

# Add the content of caddy_collabora_entry.txt to /etc/caddy/Caddyfile
cat caddy_collabora_entry.txt >> /etc/caddy/Caddyfile
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile


# if $DOMAIN = "int.de" then uncomment #tls internal
if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
fi

systemctl restart caddy



# Install in nextcloud the collabora app
sudo -u www-data php /var/www/nextcloud/occ app:install richdocuments
# We need this because if we removed it before and then reinstalled it, it is disabled:
sudo -u www-data php /var/www/nextcloud/occ app:enable richdocuments

# Configure onlyoffice
sudo -u www-data php /var/www/nextcloud/occ config:app:set richdocuments wopi_url --value="https://office.$DOMAIN/"
# if $DOMAIN = "int.de" then deactivate the certificate verification
if [ $DOMAIN = "int.de" ] ; then
  sudo -u www-data php /var/www/nextcloud/occ config:app:set richdocuments disable_certificate_verification --value="yes"
fi
