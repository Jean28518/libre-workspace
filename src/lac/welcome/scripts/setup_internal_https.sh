# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
export DEBIAN_FRONTEND=noninteractive


apt install libnss3-tools
caddy trust

mkdir -p /var/www/cert/
cp /etc/ssl/certs/Caddy_Local_Authority_* /var/www/cert/lan.crt

echo "$IP cert.$DOMAIN" >> /etc/hosts # Domain itself
samba-tool dns add la.$DOMAIN $DOMAIN cert A $IP -U administrator%$ADMIN_PASSWORD


echo "cert.int.de {
    tls internal
    root * /var/www/cert/
    file_server browse
}

" >> /etc/caddy/Caddyfile

systemctl reload caddy