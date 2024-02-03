# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP

mkdir /root/rocket.chat
cp docker_rocketchat_entry.txt /root/rocket.chat/docker-compose.yml
sed -i "s/SED_DOMAIN/$DOMAIN/g" /root/rocket.chat/docker-compose.yml
sed -i "s/SED_PASSWORD/$ADMIN_PASSWORD/g" /root/rocket.chat/docker-compose.yml

docker-compose -f /root/rocket.chat/docker-compose.yml up -d

# Add the content of caddy_rocketchat_entry.txt to /etc/caddy/Caddyfile
cat caddy_rocketchat_entry.txt >> /etc/caddy/Caddyfile
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile
if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
fi
systemctl reload caddy

apt install python3-pymongo -y
# We need to wait for the mongoDB to be ready
sleep 60
python3 ./configure_rocketchat_ldap.py