# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD

# We need to update this link with the latest stable version regularly
wget https://github.com/jitsi/docker-jitsi-meet/archive/refs/tags/stable-9078.zip
unzip stable-9078.zip
mv docker-jitsi-meet-stable-9078 /root/jitsi
rm stable-9078.zip

cp /root/jitsi/env.example /root/jitsi/.env

# Change the HTTP_PORT to 30323
sed -i "s/HTTP_PORT=8000/HTTP_PORT=30323/g" /root/jitsi/.env
# Comment out HTTPS_PORT
sed -i "s/HTTPS_PORT=8443/#HTTPS_PORT=443/g" /root/jitsi/.env
# Set PUBLIC_URL to https://meet.$DOMAIN
echo "PUBLIC_URL=https://meet.$DOMAIN" >> /root/jitsi/.env

# Comment out - '${HTTPS_PORT}:443'
sed -i "s/- '\${HTTPS_PORT}:443'/#/g" /root/jitsi/docker-compose.yml
# Comment out - '127.0.0.1:${JVB_COLIBRI_PORT:-8080}:8080'
sed -i "s/- '127.0.0.1:\${JVB_COLIBRI_PORT:-8080'/#/" /root/jitsi/docker-compose.yml

cd /root/jitsi
./gen-passwords.sh
mkdir -p ~/.jitsi-meet-cfg/{web,transcripts,prosody/config,prosody/prosody-plugins-custom,jicofo,jvb,jigasi,jibri}
docker-compose up -d
cd -

ufw allow 10000/udp


# Add the content of caddy_jitsi_entry.txt to /etc/caddy/Caddyfile
cat caddy_jitsi_entry.txt >> /etc/caddy/Caddyfile
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile
if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
fi
systemctl reload caddy
