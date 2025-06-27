#!/bin/bash

# Check if we are root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root."
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

INSTANCE_PATH="$1"
if [ -z "$INSTANCE_PATH" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

ADMIN_PASSWORD="$2"
if [ -z "$ADMIN_PASSWORD" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

ADMIN_EMAIL_ADDRESS="$3"
if [ -z "$ADMIN_EMAIL_ADDRESS" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

URL="$4"
if [ -z "$URL" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

TITLE="$5"
if [ -z "$TITLE" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

LOCALE="$6"
if [ -z "$LOCALE" ]; then
    echo "Usage: $0 <instance_path> <admin_password> <admin_email_address> <url> <title> <locale>"
    exit 1
fi

docker-compose -f "$INSTANCE_PATH/docker-compose.yml" up -d

# Change some php values for better upload and memory handling
echo "php_value upload_max_filesize 512M
php_value post_max_size 512M
php_value memory_limit 1024M
" >> $INSTANCE_PATH/html/.htaccess


# Function for running wordpress-cli commands
run_wp_cli() {
  docker run -it --rm --volumes-from wordpress_wordpress_1 \
    --network container:wordpress_wordpress_1 \
    -e WORDPRESS_DB_USER=wordpress \
    -e WORDPRESS_DB_PASSWORD=Thu8vee5 \
    -e WORDPRESS_DB_NAME=wordpress \
    -e WORDPRESS_DB_HOST=db \
    wordpress:cli "$@"
}


sleep 10 # Wait for the database to be ready

# Start the WordPress installation
wp core install \
  --url="$URL" \
  --title="$TITLE" \
  --admin_user=Administrator \
  --admin_password="$ADMIN_PASSWORD" \
  --admin_email="$ADMIN_EMAIL_ADDRESS" \
  --locale="$LOCALE" \
  --skip-email \

# Remove plugins:
rm -rf /root/wordpress/html/wp-content/plugins/hello.php
rm -rf /root/wordpress/html/wp-content/plugins/akismet
# Remove old themes:
rm -rf /root/wordpress/html/wp-content/themes/twentytwenty
rm -rf /root/wordpress/html/wp-content/themes/twentytwentyone
rm -rf /root/wordpress/html/wp-content/themes/twentytwentytwo
rm -rf /root/wordpress/html/wp-content/themes/twentytwentythree
rm -rf /root/wordpress/html/wp-content/themes/twentytwentyfour




# Enable auto updates for the litespeed cache plugin, themes, translations and core
run_wp_cli plugin auto-updates enable --all
run_wp_cli theme auto-updates enable --all