# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
# LDAP_DC


## Setup Nextcloud #########################################

apt install caddy mariadb-server php-gd php-mysql php-curl php-mbstring php-intl php-gmp php-bcmath php-imap php-xml php-bz2 php-imagick libmagickcore-6.q16-6-extra php-zip php-fpm php-redis php-apcu php-memcache php-sqlite3 php-pgsql unzip vim -y

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
systemctl reload caddy

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
sudo -u www-data php /var/www/nextcloud/occ app:install groupfolders

# Update the database because nextcloud 29.0.0 doen't add the missing indices?!
sudo -u www-data php /var/www/nextcloud/occ db:add-missing-indices


# PHP-Optimizations
# Set the php memory limit to 1024 MB
sed -i "s/memory_limit = 128M/memory_limit = 1024M/g" /etc/php/$PHP_VERSION/fpm/php.ini
# upload_max_filesize = 50 G
sed -i "s/upload_max_filesize = 2M/upload_max_filesize = 50G/g" /etc/php/$PHP_VERSION/fpm/php.ini
echo "opcache.interned_strings_buffer = 128" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "opcache.memory_consumption = 2048" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "apc.enable_cli=1" >> /etc/php/$PHP_VERSION/fpm/php.ini
# We need this for the automatic updates and the cronjob
echo "apc.enable_cli=1" >> /etc/php/$PHP_VERSION/cli/php.ini

# Uncomment the environment variables in /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[HOSTNAME\]/env[HOSTNAME]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[PATH\]/env[PATH]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[TMP\]/env[TMP]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[TMPDIR\]/env[TMPDIR]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[TEMP\]/env[TEMP]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf

systemctl restart php*


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


# Enable SSO (OIDC) for nextcloud
sudo -u www-data php /var/www/nextcloud/occ app:install oidc_login

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
cd /usr/share/linux-arbeitsplatz/
bash django_add_oidc_provider_client.sh "Nextcloud" "$CLIENT_ID" "$CLIENT_SECRET" "https://cloud.$DOMAIN/index.php/apps/oidc_login/oidc\nhttps://cloud.$DOMAIN/apps/oidc_login/oidc"
cd -


# Remove index.php from the URL:
sudo -u www-data php /var/www/nextcloud/occ config:system:set htaccess.RewriteBase --value="/"
sudo -u www-data php /var/www/nextcloud/occ maintenance:update:htaccess

# Setup error log in /var/log/php_error.log for fpm and cli
echo "" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "error_reporting = E_ALL" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "error_reporting = E_ALL" >> /etc/php/$PHP_VERSION/cli/php.ini
echo "log_errors = On" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "log_errors = On" >> /etc/php/$PHP_VERSION/cli/php.ini
echo "error_log = /var/log/php_errors.log" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "error_log = /var/log/php_errors.log" >> /etc/php/$PHP_VERSION/cli/php.ini
touch /var/log/php_errors.log
chown www-data:www-data /var/log/php_errors.log

systemctl restart php*
