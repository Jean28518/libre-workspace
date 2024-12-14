# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
# LDAP_DC

# Remove samba dc
apt purge -y acl attr samba samba-dsdb-modules samba-vfs-modules smbclient winbind libpam-winbind libnss-winbind libpam-krb5 krb5-config krb5-user dnsutils chrony net-tools samba-ad-provision
sudo apt autoremove --purge -y

# Install dnsmasq as replacement for samba dns server
apt install -y dnsmasq
echo "
listen-address=$IP" >> /etc/dnsmasq.conf
systemctl enable --now dnsmasq
systemctl restart dnsmasq

# Update cfg file:
# Remove the lines with "AUTH_LDAP" in it
sed -i "/AUTH_LDAP/d" /usr/share/linux-arbeitsplatz/cfg
sed -i "/INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP/d" /usr/share/linux-arbeitsplatz/cfg
# Add the Samba AD disabled flag to the cfg file
# Ensure that we put in a new line
echo "" >> /usr/share/linux-arbeitsplatz/cfg
echo "export AUTH_LDAP_SERVER_URI=\"\"
export INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP=\"$ADMIN_PASSWORD\"" >>/usr/share/linux-arbeitsplatz/cfg


# Remove the /root/samba_dc symbolic link
rm /root/samba_dc
# Remove the /etc/samba directory
rm -rf /etc/samba

# Reset the local Administrator by setting the password to $ADMIN_PASSWORD
cd /usr/share/linux-arbeitsplatz
bash ./django_set_local_Administrator_password.sh "$ADMIN_PASSWORD"
bash ./django_reset_2fa_for_Administrator.sh

# Restart Libre Worksapce Services
systemctl restart linux-arbeitsplatz-unix.service
systemctl restart linux-arbeitsplatz-web.service