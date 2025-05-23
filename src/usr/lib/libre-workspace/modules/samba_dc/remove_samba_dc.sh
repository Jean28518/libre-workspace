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
sed -i "/AUTH_LDAP/d" /etc/libre-workspace/portal/portal.conf
sed -i "/INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP/d" /etc/libre-workspace/portal/portal.conf
# Add the Samba AD disabled flag to the cfg file
# Ensure that we put in a new line
echo "" >> /etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_SERVER_URI=\"\"
export INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP=\"$ADMIN_PASSWORD\"" >>/etc/libre-workspace/portal/portal.conf


# Remove the /root/samba_dc symbolic link
rm /root/samba_dc
# Remove the /etc/samba directory
rm -rf /etc/samba

# Reset the local Administrator by setting the password to $ADMIN_PASSWORD
libre-workspace-set-local-admin-password "$ADMIN_PASSWORD"
libre-workspace-reset-2fa

# Restart Libre Worksapce Services
systemctl restart libre-workspace-service.service
systemctl restart libre-workspace-portal.service