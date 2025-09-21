export DEBIAN_FRONTEND=noninteractive

apt update
apt dist-upgrade -y
apt install ufw vim docker.io docker-compose apparmor htop curl -y

# Set the password of the systemv user
chpasswd <<<"systemv:$ADMIN_PASSWORD"

ufw allow http
ufw allow https
ufw allow ssh
ufw --force enable

# Remove the default caddy service if it exists
python3 ../remove_caddy_service.py :80
