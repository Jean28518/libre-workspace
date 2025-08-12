# Removes also all data!
# Needs the following variables:
# DOMAIN

libre-workspace-remove-webserver-entry element.$DOMAIN
libre-workspace-remove-webserver-entry matrix.$DOMAIN

cd /root/matrix
docker-compose down --volumes
cd -

rm -r /root/matrix
