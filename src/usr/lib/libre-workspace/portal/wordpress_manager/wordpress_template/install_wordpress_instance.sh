#!/bin/bash

# Check if we are root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root."
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
    exit 1
fi

INSTANCE_PATH="$1"
if [ -z "$INSTANCE_PATH" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
    exit 1
fi

# ADMIN_PASSWORD="$2"
# if [ -z "$ADMIN_PASSWORD" ]; then
#     echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
#     exit 1
# fi

# ADMIN_EMAIL_ADDRESS="$3"
# if [ -z "$ADMIN_EMAIL_ADDRESS" ]; then
#     echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
#     exit 1
# fi

# DOMAIN="$4"
# if [ -z "$DOMAIN" ]; then
#     echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
#     exit 1
# fi

# TITLE="$5"
# if [ -z "$TITLE" ]; then
#     echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
#     exit 1
# fi

# LOCALE="$6"
# if [ -z "$LOCALE" ]; then
#     echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
#     exit 1
# fi

# DB_PASSWORD="$7"
# if [ -z "$DB_PASSWORD" ]; then
#     echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <domain> <title> <locale> <db_password>"
#     exit 1
# fi

docker-compose -f "$INSTANCE_PATH/docker-compose.yml" up -d


# Because The docker image does not provice any cli install/provision method which works we have to sadly do it manually from here.
# For a later point of time the following code should be a good starting point to finish this auto provisioning.


# # Define the Docker container name: mysite.int.de -> mysiteintde_wordpress_1
# DOCKER_CONTAINER_NAME=$(echo "$DOMAIN" | sed 's/[^a-zA-Z0-9]//g' | tr '[:upper:]' '[:lower:]')
# DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME}_wordpress_1"

# # Function for running wordpress-cli commands
# run_wp_cli() {
#   # Echo everything for debugging
#   echo "docker run -it --rm --volumes-from $DOCKER_CONTAINER_NAME \
#     --network container:$DOCKER_CONTAINER_NAME \
#     -e WORDPRESS_DB_USER=wordpress \
#     -e WORDPRESS_DB_PASSWORD=\"$DB_PASSWORD\" \
#     -e WORDPRESS_DB_NAME=wordpress \
#     -e WORDPRESS_DB_HOST=db \
#     wordpress:cli $@" >> /tmp/mylog.txt

#   docker run -it --rm --volumes-from $DOCKER_CONTAINER_NAME \
#     --network container:$DOCKER_CONTAINER_NAME \
#     -e WORDPRESS_DB_USER=wordpress \
#     -e WORDPRESS_DB_PASSWORD=$DB_PASSWORD \
#     -e WORDPRESS_DB_NAME=wordpress \
#     -e WORDPRESS_DB_HOST=db \
#     wordpress:cli "$@"
# }


# # docker run -it --rm --volumes-from wordpress_wordpress_1        --network container:wordpress_wordpress_1       -e WORDPRESS_DB_USER=wordpress  -e WORDPRESS_DB_PASSWORD=Thu8vee5   -e WORDPRESS_DB_NAME=wordpress   -e WORDPRESS_DB_HOST=db    wordpress:cli plugin install litespeed-cache --allow-root --activate
# # docker run -it --rm --volumes-from mysiteintde_wordpress_1     --network container:mysiteintde_wordpress_1     -e WORDPRESS_DB_USER=wordpress     -e WORDPRESS_DB_PASSWORD="jttQRTr6DIlxlp2b"     -e WORDPRESS_DB_NAME=wordpress     -e WORDPRESS_DB_HOST=db     wordpress:cli core install --url=https://mysite.int.de --title=My cool Site --admin_user=Administrator --admin_password=12341234 --admin_email=martin.zie@gmx.de --locale=en_US --skip-email
# # docker run -it --rm --volumes-from mysiteintde_wordpress_1     --network container:mysiteintde_wordpress_1     -e WORDPRESS_DB_USER=wordpress     -e WORDPRESS_DB_PASSWORD="jttQRTr6DIlxlp2b"     -e WORDPRESS_DB_NAME=wordpress     -e WORDPRESS_DB_HOST=db     wordpress:cli theme auto-updates enable --all
# /usr/local/bin/docker-entrypoint.sh: exec: line 11: theme: not found
# /usr/local/bin/docker-entrypoint.sh: exec: line 11: core: not found

# sleep 10 # Wait for the database to be ready

# # Download the latest version of wordpress manually:
# wget https://wordpress.org/latest.zip -O /tmp/wordpress.zip

# rm -r $INSTANCE_PATH/html/*

# # Unzip the downloaded wordpress files to the instance path
# unzip -q /tmp/wordpress.zip -d /tmp/
# cp -r /tmp/wordpress/* $INSTANCE_PATH/html/



# # Setup wordpress config file
# run_wp_cli config create \
#   --dbname=wordpress \
#   --dbuser=wordpress \
#   --dbpass="$DB_PASSWORD" \
#   --dbhost=db \
#   --path="/var/www/html" \
#   --skip-check

# --dbname=wordpress  --dbuser=wordpress --dbpass="$DB_PASSWORD" --dbhost=db --path="/var/www/html" --skip-check

# # Start the WordPress installation
# run_wp_cli core install \
#   --url="https://$DOMAIN" \
#   --title=\"$TITLE\" \
#   --admin_user=Administrator \
#   --admin_password="$ADMIN_PASSWORD" \
#   --admin_email="$ADMIN_EMAIL_ADDRESS" \
#   --locale="$LOCALE" \
#   --skip-email


# # Remove plugins:
# rm -rf /root/wordpress/html/wp-content/plugins/hello.php
# rm -rf /root/wordpress/html/wp-content/plugins/akismet
# # Remove old themes:
# rm -rf /root/wordpress/html/wp-content/themes/twentytwenty
# rm -rf /root/wordpress/html/wp-content/themes/twentytwentyone
# rm -rf /root/wordpress/html/wp-content/themes/twentytwentytwo
# rm -rf /root/wordpress/html/wp-content/themes/twentytwentythree
# rm -rf /root/wordpress/html/wp-content/themes/twentytwentyfour




# # Enable auto updates for the litespeed cache plugin, themes, translations and core
# run_wp_cli plugin auto-updates enable --all
# run_wp_cli theme auto-updates enable --all




# # Change some php values for better upload and memory handling
# echo "php_value upload_max_filesize 512M
# php_value post_max_size 512M
# php_value memory_limit 1024M
# " >> $INSTANCE_PATH/html/.htaccess