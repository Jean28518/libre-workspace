# This script should be run as root
# We need these variables:
# DOMAIN (this doesn't change)
# IP
# ADMIN_PASSWORD

# Change password of the ldap Administrator user in /root/matrix/synapse-data/homeserver.yaml
sed -i "s/bind_password:.*/bind_password: \"$ADMIN_PASSWORD\"/g" /root/matrix/synapse-data/homeserver.yaml

# Change uri in /root/matrix/synapse-data/homeserver.yaml
sed -i "s/uri:.*/uri: \"ldaps:\/\/$IP:636\"/g" /root/matrix/synapse-data/homeserver.yaml