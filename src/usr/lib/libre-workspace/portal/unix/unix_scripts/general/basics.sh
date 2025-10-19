export DEBIAN_FRONTEND=noninteractive

apt update
apt dist-upgrade -y
apt install ufw vim docker.io docker-compose docker-cli apparmor htop curl php-fpm mariadb-server -y

# Set the password of the systemv user
chpasswd <<<"systemv:$ADMIN_PASSWORD"

ufw allow http
ufw allow https
ufw allow ssh
ufw --force enable

# Remove the default caddy service if it exists
python3 libre-workspace-remove-webserver-entry :80
