# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP

# Thrd Level:                                       # subdomain
SCND_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f1`    # int
FRST_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f2`    # de

DEBIAN_FRONTEND=noninteractive

# Install portal
apt install php-fpm git -y
cd /var/www/
git clone https://github.com/Jean28518/linux-arbeitsplatz-portal.git
cd -

# Add access page reverse proxy on ip address
echo "$IP {
    #tls internal
    handle_path /static* {
        root * /var/www/linux-arbeitsplatz-static
        file_server
        encode zstd gzip
    } 
    handle {
    rewrite * /welcome/access
    reverse_proxy localhost:11123
    }
}

" >> /etc/hosts

cat caddy_portal_entry.txt >> /etc/caddy/Caddyfile
if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
  sed -i "s/SED_DOMAIN_DELETE_PUBLIC/$DOMAIN/g" /etc/caddy/Caddyfile
else 
  sed -i "s/SED_DOMAIN_DELETE_PUBLIC//g" /etc/caddy/Caddyfile
fi
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile


systemctl reload caddy

# Change the linux arbeits zentrale to the finished domain in the caddyfile to central.$DOMAIN
sed -i "s/:443/central.$DOMAIN/g" /etc/caddy/Caddyfile 

# Set the cfg file of lac:
# LINUX_ARBEITSPLATZ_CONFIGURED=False to LINUX_ARBEITSPLATZ_CONFIGURED=True
sed -i "s/LINUX_ARBEITSPLATZ_CONFIGURED=False/LINUX_ARBEITSPLATZ_CONFIGURED=True/g" /usr/share/linux-arbeitsplatz/cfg

# Remove the lines with "EMAIL" in it
sed -i "/EMAIL/d" /usr/share/linux-arbeitsplatz/cfg

# Remove the lines with "AUTH_LDAP" in it
sed -i "/AUTH_LDAP/d" /usr/share/linux-arbeitsplatz/cfg

# Add the EMAIL settings to the cfg file
echo "export EMAIL_HOST=\"$EMAIL_HOST\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export EMAIL_PORT=\"$EMAIL_PORT\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export EMAIL_HOST_USER=\"$EMAIL_HOST_USER\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export EMAIL_HOST_PASSWORD=\"$EMAIL_HOST_PASSWORD\"" >>/usr/share/linux-arbeitsplatz/cfg
if [ $MAIL_ENCRYPTION = "tls" ] ; then
  echo "export EMAIL_USE_TLS=True" >>/usr/share/linux-arbeitsplatz/cfg
else
  echo "export EMAIL_USE_SSL=True" >>/usr/share/linux-arbeitsplatz/cfg
fi

# Add the Samba AD settings to the cfg file
echo "export AUTH_LDAP_SERVER_URI=\"ldaps://la.$DOMAIN\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_DC=\"dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_BIND_DN=\"cn=Administrator,cn=users,dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_BIND_PASSWORD=\"$ADMIN_PASSWORD\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_USER_DN_TEMPLATE=\"cn=%(user)s,cn=users,dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_GROUP_SEARCH_BASE=\"cn=Groups,dc=$SCND_DOMAIN_LABEL,dc=$FRST_DOMAIN_LABEL\"" >>/usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_GROUP_ADMIN_DN=\"CN=Administrators,CN=Builtin,DC=$SCND_DOMAIN_LABEL,DC=$FRST_DOMAIN_LABEL\"" >>/usr/share/linux-arbeitsplatz/cfg

# Set the password of the systemv user
chpasswd <<<"systemv:$ADMIN_PASSWORD"

# Enable the unix service
/usr/bin/systemctl enable linux-arbeitsplatz-unix.service

rm installation_running

# After everything is configured, we need to restart the whole server
reboot
