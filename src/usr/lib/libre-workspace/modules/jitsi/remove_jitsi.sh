# Removes also all data!
# Needs the following variables:
# DOMAIN

libre-workspace-remove-webserver-entry meet.$DOMAIN

cd /root/jitsi
docker-compose down --volumes
cd -

ufw delete allow 10000/udp
rm -r ~/.jitsi-meet-cfg/
rm -r /root/jitsi
