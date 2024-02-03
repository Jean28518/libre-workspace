# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD

SCND_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f1`
FRST_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f2`
DC_DC="dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL"

# Install matrix
mkdir /root/matrix
cp docker_matrix_entry.txt /root/matrix/docker-compose.yml

mkdir /root/matrix/synapse-data
docker run --rm --volume /root/matrix/synapse-data:/data -e SYNAPSE_SERVER_NAME=matrix.$DOMAIN -e SYNAPSE_REPORT_STATS=no matrixdotorg/synapse:latest generate


echo "
modules:
 - module: \"ldap_auth_provider.LdapAuthProviderModule\"
   config:
     enabled: true
     uri: \"ldaps://$IP:636\"
     start_tls: false
     base: \"dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL\"
     attributes:
        uid: \"cn\"
        mail: \"mail\"
        name: \"displayName\"
     bind_dn: \"cn=Administrator,cn=users,dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL\"
     bind_password: \"$ADMIN_PASSWORD\"
     #filter: \"(objectClass=posixAccount)\"
     tls_options:
       validate: false" >> /root/matrix/synapse-data/homeserver.yaml


# Delete the line which starts with databas: and is 3 lines long
sed -i "/database:/,+3d" /root/matrix/synapse-data/homeserver.yaml

# Add the database settings to the homeserver.yaml
echo "database:
  name: psycopg2
  args:
    user: synapse
    password: OoRei7oh
    dbname: synapse
    host: db
    cp_min: 5
    cp_max: 10" >> /root/matrix/synapse-data/homeserver.yaml

# Run docker-compose.yml
# We mv this signing key because otherwise synapse will complain about the signing key. I don't know why.
mv /root/matrix/synapse-data/matrix.$DOMAIN.signing.key /root/matrix/synapse-data/matrix.$DOMAIN.signing.key.old
docker-compose -f /root/matrix/docker-compose.yml up -d

# If synapse is restarting and complaining about the signing key (Permission denied), then run this command:
# mv /root/matrix/synapse-data/signing.key /root/matrix/synapse-data/signing.key.old


. update_element_config.sh


# Add caddy file entry:
echo "matrix.$DOMAIN {
    #tls internal
    reverse_proxy localhost:8008
}

" >> /etc/caddy/Caddyfile

echo "element.$DOMAIN {
    #tls internal
    reverse_proxy localhost:15124
}

" >> /etc/caddy/Caddyfile

systemctl reload caddy