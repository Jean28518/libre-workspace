# This script should be run as root
# We need these variables:
# DOMAIN (this doesn't change)
# IP
# ADMIN_PASSWORD

# Change password of the nextcloud Administrator user
export OC_PASS=$ADMIN_PASSWORD
sudo -u www-data php /var/www/nextcloud/occ user:resetpassword --password-from-env Administrator

# Change password of the ldap Administrator user
sudo -u www-data php /var/www/nextcloud/occ ldap:set-config s01 ldapAgentPassword "$ADMIN_PASSWORD"

# Update trusted proxies
sudo -u www-data php /var/www/nextcloud/occ config:system:set trusted_proxies 0 --value=$IP