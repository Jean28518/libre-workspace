#!/bin/bash

INSTANCE_PATH="$1"
if [ -z "$INSTANCE_PATH" ]; then
    echo "Usage: $0 <instance_path> <db_password> <domain>"
    exit 1
fi

DB_PASSWORD="$2"
if [ -z "$DB_PASSWORD" ]; then
    echo "Usage: $0 <instance_path> <db_password> <domain>"
    exit 1
fi

DOMAIN="$3"
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <instance_path> <db_password> <domain>"
    exit 1
fi

# Remove plugins:
rm -rf /root/wordpress/html/wp-content/plugins/hello.php
rm -rf /root/wordpress/html/wp-content/plugins/akismet
# Remove old themes:
rm -rf /root/wordpress/html/wp-content/themes/twentytwenty
rm -rf /root/wordpress/html/wp-content/themes/twentytwentyone
rm -rf /root/wordpress/html/wp-content/themes/twentytwentytwo
rm -rf /root/wordpress/html/wp-content/themes/twentytwentythree
rm -rf /root/wordpress/html/wp-content/themes/twentytwentyfour

DOCKER_CONTAINER_NAME=$(echo "$DOMAIN" | sed 's/[^a-zA-Z0-9]//g' | tr '[:upper:]' '[:lower:]')
DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME}_wordpress_1"

run_wp_cli() {
  docker run -it --rm --volumes-from $DOCKER_CONTAINER_NAME \
    --network container:$DOCKER_CONTAINER_NAME \
    -e WORDPRESS_DB_USER=wordpress \
    -e WORDPRESS_DB_PASSWORD=$DB_PASSWORD \
    -e WORDPRESS_DB_NAME=wordpress \
    -e WORDPRESS_DB_HOST=db \
    wordpress:cli "$@"
}

# Enable auto updates for the litespeed cache plugin, themes, translations and core
run_wp_cli plugin auto-updates enable --all
run_wp_cli theme auto-updates enable --all

# Run update for all plugins, themes, core and translations
run_wp_cli plugin update --all
run_wp_cli theme update --all
run_wp_cli core update
run_wp_cli language core update




# Change some php values for better upload and memory handling, if not already set
if [ "$(grep -c 'upload_max_filesize' $INSTANCE_PATH/html/.htaccess)" -eq 0 ]; then
    echo "Adding PHP values to .htaccess"
    echo "php_value upload_max_filesize 512M
php_value post_max_size 512M
php_value memory_limit 1024M
" >> $INSTANCE_PATH/html/.htaccess
else
    echo "PHP values already set in .htaccess, skipping..."
fi


