export DEBIAN_FRONTEND=noninteractive

apt update
apt dist-upgrade -y
apt install ufw vim docker.io docker-compose apparmor htop -y

ufw allow http
ufw allow https
ufw allow ssh
ufw --force enable

