#!/bin/bash

export LC_ALL=C

# Get PHP-Version
PHP_VERSION=`php -v | head -n 1 | cut -d " " -f 2 | cut -d "." -f 1,2`

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


# PHP-Optimizations
# Set the php memory limit to 1024 MB
sed -i "s/^memory_limit = .*/memory_limit = 1024M/g" /etc/php/$PHP_VERSION/fpm/php.ini
# upload_max_filesize = 50 G
sed -i "s/^upload_max_filesize = .*/upload_max_filesize = 50G/g" /etc/php/$PHP_VERSION/fpm/php.ini
sed -i "s/^post_max_size = .*/post_max_size = 50G/g" /etc/php/$PHP_VERSION/fpm/php.ini
echo "opcache.interned_strings_buffer = 128" >> /etc/php/$PHP_VERSION/fpm/php.ini
echo "opcache.memory_consumption = 2048" >> /etc/php/$PHP_VERSION/fpm/php.ini

# If RAM is under 3G then we change the opcache.memory_consumption
if [ $(free -m | awk '/^Mem:/{print $2}') -lt 3072 ]; then
    echo "Reducing opcache.memory_consumption to 1024 because low RAM detected"
    sed -i "s/opcache.memory_consumption = 2048/opcache.memory_consumption = 1024/g" /etc/php/$PHP_VERSION/fpm/php.ini
fi

echo "apc.enable_cli=1" >> /etc/php/$PHP_VERSION/fpm/php.ini
# We need this for the automatic updates and the cronjob
echo "apc.enable_cli=1" >> /etc/php/$PHP_VERSION/cli/php.ini

# Uncomment the environment variables in /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[HOSTNAME\]/env[HOSTNAME]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[PATH\]/env[PATH]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[TMP\]/env[TMP]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[TMPDIR\]/env[TMPDIR]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf
sed -i "s/;env\[TEMP\]/env[TEMP]/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf

# Update pm.max_children
# Available RAM:
AVAILABLE_RAM=$(free -m | awk '/^Mem:/{print $2}')
# PM_MAX_CHILDREN = Memory / 100 MB * 0.8
PM_MAX_CHILDREN=$((AVAILABLE_RAM / 100 * 4/5))
echo "Setting pm.max_children to $PM_MAX_CHILDREN"
sed -i "s/^pm.max_children = .*/pm.max_children = $PM_MAX_CHILDREN/g" /etc/php/$PHP_VERSION/fpm/pool.d/www.conf

systemctl restart php$PHP_VERSION-fpm.service