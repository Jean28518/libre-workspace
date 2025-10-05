# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
# LDAP_DC


## Setup Nextcloud #########################################

apt install caddy mariadb-server php-gd php-mysql php-curl php-mbstring php-intl php-gmp php-bcmath php-xml php-bz2 php-imagick libmagickcore-7.q16-10-extra php-zip php-fpm php-redis php-apcu php-memcache php-sqlite3 php-pgsql unzip vim -y

# Get PHP-Version
PHP_VERSION=`php -v | head -n 1 | cut -d " " -f 2 | cut -d "." -f 1,2`

# Setup mysql database
mysql --execute "CREATE USER 'nextcloud'@'localhost' IDENTIFIED BY 'eemoi2Sh';"
mysql --execute "CREATE DATABASE IF NOT EXISTS nextcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
mysql --execute "GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'localhost';"
mysql --execute "FLUSH PRIVILEGES;"

# Setup nextcloud
wget https://download.nextcloud.com/server/releases/latest.zip
unzip latest.zip
mkdir -p /var/www/
mv nextcloud /var/www/nextcloud
chown -R www-data:www-data /var/www/nextcloud
rm latest.zip

# Add the content of caddy_nextcloud_entry.txt to /etc/caddy/Caddyfile
cat caddy_nextcloud_entry.txt >> /etc/caddy/Caddyfile
# If $DOMAIN is  "int.de" then uncomment #tls internal
if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
fi
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile

ufw allow http
ufw allow https
systemctl restart caddy

ADDITIONAL_INSTALL_OPTIONS=""
# if /data exists, then add --data-dir="/data/nextcloud" to the installation options
if [ -d "/data" ]; then
  ADDITIONAL_INSTALL_OPTIONS="--data-dir=/data/nextcloud"
  mkdir -p /data/nextcloud
  chown -R www-data:www-data /data/nextcloud
  # We also need to change the permissions of the data folder becouse otherwise caddy can't access it properly
  chown -R www-data:www-data /data
fi

# Configure nextcloud
sudo -u www-data php /var/www/nextcloud/occ maintenance:install --database "mysql" --database-name "nextcloud"  --database-user "nextcloud" --database-pass "eemoi2Sh" --admin-user "Administrator" --admin-pass "$ADMIN_PASSWORD" $ADDITIONAL_INSTALL_OPTIONS
# Add cloud.$DOMAIN to trusted domains
sudo -u www-data php /var/www/nextcloud/occ config:system:set trusted_domains 1 --value=cloud.$DOMAIN
# Add $IP to tusted_proxies
sudo -u www-data php /var/www/nextcloud/occ config:system:set trusted_proxies 0 --value=$IP
# Set the default phone region to Germany
sudo -u www-data php /var/www/nextcloud/occ config:system:set default_phone_region --value=DE
# Set maintenance window start
sudo -u www-data php /var/www/nextcloud/occ config:system:set maintenance_window_start --value=1
# Disable all default files for a new user
sudo -u www-data php /var/www/nextcloud/occ config:system:set skeletondirectory --value=""


# Disable the dashboard app
sudo -u www-data php /var/www/nextcloud/occ app:disable dashboard
sudo -u www-data php /var/www/nextcloud/occ app:disable activity
sudo -u www-data php /var/www/nextcloud/occ app:disable firstrunwizard
sudo -u www-data php /var/www/nextcloud/occ app:disable support
sudo -u www-data php /var/www/nextcloud/occ app:disable nextcloud_announcements


# Install Apps:
sudo -u www-data php /var/www/nextcloud/occ app:install calendar
sudo -u www-data php /var/www/nextcloud/occ app:install contacts
sudo -u www-data php /var/www/nextcloud/occ app:install deck
sudo -u www-data php /var/www/nextcloud/occ app:install mail
sudo -u www-data php /var/www/nextcloud/occ app:install notes
sudo -u www-data php /var/www/nextcloud/occ app:install tasks
sudo -u www-data php /var/www/nextcloud/occ app:install collectives
sudo -u www-data php /var/www/nextcloud/occ app:install drawio
sudo -u www-data php /var/www/nextcloud/occ app:install secrets
sudo -u www-data php /var/www/nextcloud/occ app:install groupfolders

# Update the database because nextcloud 29.0.0 doen't add the missing indices?!
sudo -u www-data php /var/www/nextcloud/occ db:add-missing-indices

. /usr/lib/libre-workspace/modules/nextcloud/set_php_variables.sh


# Setup cronjob
crontab -u www-data -l > /tmp/crontab
echo "*/5  *  *  *  * php -f /var/www/nextcloud/cron.php" >> /tmp/crontab
crontab -u www-data /tmp/crontab

# Install php-ldap for compatibility with samba-dc (sometimes we need this because of old libre workspace migratione, etc.)
apt install php-ldap -y
systemctl restart php*

# Add nextcloud to samba-dc active directory
# sudo -u www-data php /var/www/nextcloud/occ app:enable user_ldap
# sudo -u www-data php /var/www/nextcloud/occ ldap:create-empty-config
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapHost ldaps://la.$DOMAIN
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapPort 636
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapBase "$LDAP_DC"
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapBaseGroups "cn=users,$LDAP_DC"
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapBaseUsers "cn=users,$LDAP_DC"
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapAgentName "cn=Administrator,cn=users,$LDAP_DC"
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapAgentPassword "$ADMIN_PASSWORD"
# # Disable the ssl certificate validation
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 turnOffCertCheck 1
# # custom ldap request (user search filter)
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapUserFilter "(objectclass=*)"
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapLoginFilter "(&(objectclass=*)(|(cn=%uid)(|(mailPrimaryAddress=%uid)(mail=%uid))))"
# # custom ldap request (group search filter)
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapGroupFilter "(&(|(objectclass=group)))"
# # Group member association member(AD)
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapGroupMemberAssocAttr "member"
# # mail field
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapEmailAttribute "mail"
# # Set configuration active
# sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapConfigurationActive 1


# Enable SSO (OIDC) for nextcloud (also if its not tested for the currect nextcloud version, it should work)
sudo -u www-data php /var/www/nextcloud/occ app:install oidc_login --force
sudo -u www-data php /var/www/nextcloud/occ app:enable oidc_login --force
# Restart redis and php-fpm to make sure everything is fresh (oidc_login needs those restarts)
systemctl restart redis.service php*fpm.service

CLIENT_ID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
CLIENT_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_client_id --value="$CLIENT_ID"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_client_secret --value="$CLIENT_SECRET"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_provider_url --value="https://portal.$DOMAIN/openid"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_end_session_redirect --value=true
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_logout_url --value="https://cloud.$DOMAIN/apps/oidc_login/oidc"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_auto_redirect --value=true
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_redir_fallback --value=true
# sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes --value='{"id":"preferred_username","mail":"email","name":"name","ldap_uid":"preferred_username"}'
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes id --value="preferred_username"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes mail --value="email"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes name --value="name"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes ldap_uid --value="preferred_username"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes groups --value="groups"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_attributes is_admin --value="admin"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_scope --value="openid profile email guid groups admin"
sudo -u www-data php /var/www/nextcloud/occ config:system:set allow_user_to_change_display_name --value=
sudo -u www-data php /var/www/nextcloud/occ config:system:set lost_password_link --value="disabled"
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_hide_password_form --value=
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_disable_registration --value=
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_create_groups --value=true
sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_proxy_ldap --value= # Set this to true this if your instance has ldap enabled
if [ $DOMAIN = "int.de" ]; then
  sudo -u www-data php /var/www/nextcloud/occ config:system:set oidc_login_tls_verify --value=false
fi

# Add the oidc client to the oidc provider
libre-workspace-add-oidc-client "Nextcloud" "$CLIENT_ID" "$CLIENT_SECRET" "https://cloud.$DOMAIN/index.php/apps/oidc_login/oidc\nhttps://cloud.$DOMAIN/apps/oidc_login/oidc"


# Remove index.php from the URL:
sudo -u www-data php /var/www/nextcloud/occ config:system:set htaccess.RewriteBase --value="/"
sudo -u www-data php /var/www/nextcloud/occ maintenance:update:htaccess

## Install Redis:

# Install redis and php packages
apt-get install redis php-redis php-apcu php-memcache pwgen -y

# Set redis password
REDIS_PASSWORD=$(pwgen -n 20 1)
echo "" >> /etc/redis/redis.conf
echo "requirepass $REDIS_PASSWORD" >> /etc/redis/redis.conf

# Enable redis and restart it
systemctl enable redis-server
systemctl restart redis-server

# Configure nextcloud to use redis
# Disable all caches that nextcloud doesn't fail while we are changing the cache settings
sudo -u www-data php /var/www/nextcloud/occ config:system:delete memcache.local
sudo -u www-data php /var/www/nextcloud/occ config:system:delete memcache.distributed
sudo -u www-data php /var/www/nextcloud/occ config:system:delete memcache.locking

sudo -u www-data php /var/www/nextcloud/occ config:system:set redis host --value localhost
sudo -u www-data php /var/www/nextcloud/occ config:system:set redis port --value 6379
sudo -u www-data php /var/www/nextcloud/occ config:system:set redis dbindex --value 0
sudo -u www-data php /var/www/nextcloud/occ config:system:set redis password --value "$REDIS_PASSWORD"
sudo -u www-data php /var/www/nextcloud/occ config:system:set memcache.locking --value '\OC\Memcache\Redis'
sudo -u www-data php /var/www/nextcloud/occ config:system:set memcache.distributed --value '\OC\Memcache\Redis'
# We set the local cache to APCu, because it is faster than redis for local cache
sudo -u www-data php /var/www/nextcloud/occ config:system:set memcache.local --value '\OC\Memcache\APCu'

# Restart php
systemctl restart php*



# Fix MIME types and other issues
sudo -u www-data php /var/www/nextcloud/occ maintenance:repair --include-expensive