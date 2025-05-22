# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
# LDAP_DC

# Install matrix
mkdir /root/matrix
cp docker_matrix_entry.txt /root/matrix/docker-compose.yml

sed -i "s/SED_IP/$IP/g" /root/matrix/docker-compose.yml

mkdir /root/matrix/synapse-data
docker run --rm --volume /root/matrix/synapse-data:/data -e SYNAPSE_SERVER_NAME=matrix.$DOMAIN -e SYNAPSE_REPORT_STATS=no matrixdotorg/synapse:latest generate

# Add LDAP authentication to homeserver.yaml for local domain
if [ $DOMAIN = "int.de" ]; then
  echo "
modules:
 - module: \"ldap_auth_provider.LdapAuthProviderModule\"
   config:
     enabled: true
     uri: \"ldaps://$IP:636\"
     start_tls: false
     base: \"$LDAP_DC\"
     attributes:
        uid: \"cn\"
        mail: \"mail\"
        name: \"displayName\"
     bind_dn: \"cn=Administrator,cn=users,$LDAP_DC\"
     bind_password: \"$ADMIN_PASSWORD\"
     #filter: \"(objectClass=posixAccount)\"
     tls_options:
       validate: false" >> /root/matrix/synapse-data/homeserver.yaml
fi

if [ $DOMAIN != "int.de" ]; then
  # Add SSO to homeserver.yaml for public domain (because f****** synapse reports timeouts against portal.int.de and we don't know why)
  CLIENT_ID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
  CLIENT_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
  echo "
oidc_providers:
  - idp_id: libreworkspace
    idp_name: \"Libre Workspace\"
    issuer: \"https://portal.$DOMAIN/openid\"
    client_id: \"$CLIENT_ID\"
    client_secret: \"$CLIENT_SECRET\"
    scopes: [\"openid\", \"profile\", \"email\", \"groups\", \"guid\"]
    user_profile_method: \"userinfo_endpoint\"
    allow_existing_users: true
    user_mapping_provider:
      config:
        localpart_template: \"{{ user.preferred_username }}\"
        display_name_template: \"{{ user.name }}\"" >> /root/matrix/synapse-data/homeserver.yaml

  # if [ $DOMAIN = "int.de" ]; then
  #   echo "    skip_verification: true" >> /root/matrix/synapse-data/homeserver.yaml
  # fi

  # Add the oidc client to the oidc provider
  cd /usr/share/linux-arbeitsplatz/
  bash django_add_oidc_provider_client.sh "Matrix" "$CLIENT_ID" "$CLIENT_SECRET" "https://matrix.$DOMAIN/_synapse/client/oidc/callback"
  cd -
fi


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


# Add user directory to homeserver.yaml
echo "
user_directory:
  enabled: true
  search_all_users: true
  prefer_local_users: true

" >> /root/matrix/synapse-data/homeserver.yaml

# Run docker-compose.yml
# We mv this signing key because otherwise synapse will complain about the signing key. I don't know why.
mv /root/matrix/synapse-data/matrix.$DOMAIN.signing.key /root/matrix/synapse-data/matrix.$DOMAIN.signing.key.old
docker-compose -f /root/matrix/docker-compose.yml up -d

# If synapse is restarting and complaining about the signing key (Permission denied), then run this command:
# mv /root/matrix/synapse-data/signing.key /root/matrix/synapse-data/signing.key.old


. update_element_config.sh

# Add "unencrypt" message to clients in .well-known/matrix/server
# So the clients don't encrypt the messages by default
mkdir -p /var/www/matrix/.well-known/matrix
echo "{
    \"io.element.e2ee\": {
        \"default\": false
    }
}

" > /var/www/matrix/.well-known/matrix/client

chown -R www-data:www-data /var/www/matrix


# Add caddy file entry:
echo "matrix.$DOMAIN {
  #tls internal
  handle_path /.well-known* {
    header {
      Access-Control-Allow-Origin *
    }
    root * /var/www/matrix/.well-known
    file_server
  }
  reverse_proxy localhost:8008
}

" >> /etc/caddy/Caddyfile

echo "element.$DOMAIN {
  #tls internal
  reverse_proxy localhost:15124
}

" >> /etc/caddy/Caddyfile

# if $DOMAIN == int.de then we need to uncomment the tls internal line
if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
fi

systemctl restart caddy