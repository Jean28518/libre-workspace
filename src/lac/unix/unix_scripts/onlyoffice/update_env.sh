# This script should be run as root
# We need these variables:
# DOMAIN (this doesn't change)
# IP
# ADMIN_PASSWORD

echo "docker pull onlyoffice/documentserver:latest
docker run -i -t -d -p 10923:80 --restart=unless-stopped --name onlyoffice -e JWT_ENABLED='true' -e JWT_SECRET='$ADMIN_PASSWORD' onlyoffice/documentserver:latest --add-host cloud.$DOMAIN:$IP" > /root/onlyoffice/run.sh

docker rm -f onlyoffice
bash /root/onlyoffice/run.sh