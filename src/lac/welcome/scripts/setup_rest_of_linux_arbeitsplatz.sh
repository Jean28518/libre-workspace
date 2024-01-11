# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP

# Thrd Level:                                       # subdomain
SCND_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f1`    # int
FRST_DOMAIN_LABEL=`echo $DOMAIN | cut -d'.' -f2`    # de

DEBIAN_FRONTEND=noninteractive

# Remove the the block which begins with "# SED-LOCALHOST-ENTRY" and is 10 lines long
sed -i "/# SED-LOCALHOST-ENTRY/,+10d" /etc/caddy/Caddyfile

# Add access page reverse proxy on ip address
echo "$IP http://localhost {
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

" >> /etc/caddy/Caddyfile

if [ $DOMAIN = "int.de" ] ; then
  sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
  sed -i "s/SED_DOMAIN_DELETE_PUBLIC/$DOMAIN/g" /etc/caddy/Caddyfile
else 
  sed -i "s/SED_DOMAIN_DELETE_PUBLIC//g" /etc/caddy/Caddyfile
fi
sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile


systemctl reload caddy


# Change the linux arbeits zentrale to the finished domain in the caddyfile to portal.$DOMAIN
sed -i "s/:443/portal.$DOMAIN/g" /etc/caddy/Caddyfile 

# Set the cfg file of lac:
# LINUX_ARBEITSPLATZ_CONFIGURED=False to LINUX_ARBEITSPLATZ_CONFIGURED=True
sed -i "s/LINUX_ARBEITSPLATZ_CONFIGURED=False/LINUX_ARBEITSPLATZ_CONFIGURED=True/g" /usr/share/linux-arbeitsplatz/cfg

# Remove the lines with "EMAIL" in it
sed -i "/EMAIL/d" /usr/share/linux-arbeitsplatz/cfg

# Remove the lines with "AUTH_LDAP" in it
sed -i "/AUTH_LDAP/d" /usr/share/linux-arbeitsplatz/cfg

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
