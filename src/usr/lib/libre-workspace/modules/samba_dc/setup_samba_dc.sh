# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
# LDAP_DC
# SHORTEND_DOMAIN

# If samba-tool is installed, abort the setup because wo don't want to overwrite it at this state.
if [ -f /usr/bin/samba-tool ]; then
    echo "Samba DC is already installed. Aborting setup. Remove all samba components first before running this script."
    exit 0
fi

export DEBIAN_FRONTEND=noninteractive

## Setup DNS-Environment ##################################
hostnamectl set-hostname la
# if la.$DOMAIN is not in /etc/hosts, add it
if ! grep -q "la.$DOMAIN" /etc/hosts; then
    echo "$IP la.$DOMAIN la.$SHORTEND_DOMAIN la" >> /etc/hosts # IP of the server itself
fi

# For ubuntu systems
systemctl disable --now systemd-resolved

# Make sure we don't have dnsmasq installed
sudo apt purge dnsmasq -y

# Prepare resolv.conf
chattr -i -a /etc/resolv.conf
rm -f /etc/resolv.conf
touch /etc/resolv.conf
echo "nameserver $IP" >> /etc/resolv.conf # This is the IP of the server itself. Needed for docker containers e.g.
# Check if IP is IPv6 and add appropriate entry to resolv.conf
if [[ $IP =~ : ]]; then
    echo "nameserver 2620:fe::fe" >> /etc/resolv.conf # Quad9 IPv6
else
    echo "nameserver 9.9.9.9" >> /etc/resolv.conf # Quad9 IPv4
fi
chattr +i +a /etc/resolv.conf

## Setup SAMBA DC #########################################

# We need to set this variables that the krb5-config package does not ask for them
export REALM=$SHORTEND_DOMAIN
export KDC=la.$DOMAIN
export ADMIN_SERVER=la.$DOMAIN
apt update 
apt install -y acl attr samba samba-ad-dc samba-dsdb-modules samba-vfs-modules smbclient winbind libpam-winbind libnss-winbind libpam-krb5 krb5-config krb5-user dnsutils chrony net-tools samba-ad-provision

systemctl disable --now smbd nmbd winbind
systemctl unmask samba-ad-dc
systemctl enable samba-ad-dc

mv /etc/samba/smb.conf /etc/samba/smb.conf.bak
# Wee need to set this variables that the samba config script does not ask for them
# Host-Role
export SAMBA_HOST_ROLE=dc
# DNS Backend
export SAMBA_DNS_BACKEND=SAMBA_INTERNAL
# DNS Forwarder (Quad Nine)
export SAMBA_DNS_FORWARDER=9.9.9.9
# Administrator password
export SAMBA_ADMIN_PASSWORD=$ADMIN_PASSWORD


# SAMBA_DOMAIN should be in uppercase without the TLD for the realm
# Example: DOMAIN=libreoffice.org -> SAMBA_DOMAIN=LIBREOFFICE
export SAMBA_DOMAIN=$(echo $SHORTEND_DOMAIN | cut -d'.' -f1 | tr '[:lower:]' '[:upper:]')

samba-tool domain provision --realm=$SHORTEND_DOMAIN --domain=$SAMBA_DOMAIN --adminpass=$ADMIN_PASSWORD

mv /etc/krb5.conf /etc/krb5.conf.orig
cp /var/lib/samba/private/krb5.conf /etc/krb5.conf

systemctl start samba-ad-dc


# Configuration for the password policy
samba-tool domain passwordsettings set --complexity=off
samba-tool domain passwordsettings set --history-length=0
samba-tool domain passwordsettings set --min-pwd-age=0
samba-tool domain passwordsettings set --max-pwd-age=0


# Enable LDAPS:
mkdir -p /etc/samba/tls/
cd /etc/samba/tls/

subj="
C=DE
ST=BV
O=Nbg
localityName=Nuremberg
commonName=*.$DOMAIN
organizationalUnitName=Libre Workspace
emailAddress=webmaster@$DOMAIN
"

openssl req -newkey rsa:2048 -keyout myKey.pem -nodes -x509 -days 36500 -out myCert.pem -subj "$(echo -n "$subj" | tr "\n" "/")"

chmod 600 myKey.pem

cd -

# In the /etc/samba/smb.conf we want to append the following lines:
# [global]
# tls enabled  = yes
# tls keyfile  = /etc/samba/tls/myKey.pem
# tls certfile = /etc/samba/tls/myCert.pem
# tls cafile   =

echo "[global]" >> /etc/samba/smb.conf
sed -i "s/dns forwarder/#dns forwarder/g" /etc/samba/smb.conf
echo "dns forwarder = 9.9.9.9" >> /etc/samba/smb.conf
echo "tls enabled  = yes" >> /etc/samba/smb.conf
echo "tls keyfile  = /etc/samba/tls/myKey.pem" >> /etc/samba/smb.conf
echo "tls certfile = /etc/samba/tls/myCert.pem" >> /etc/samba/smb.conf
echo "tls cafile   =" >> /etc/samba/smb.conf

# Add the certificate to the system
cp /etc/samba/tls/myCert.pem /usr/local/share/ca-certificates/samba.crt
update-ca-certificates

# Restart samba
systemctl restart samba-ad-dc

# Allow ldaps in the firewall
ufw allow ldaps
# Allow DNS in the firewall if we are running in int.de mode
# Because of <https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Cyber-Sicherheitslage/Reaktion/CERT-Bund/CERT-Bund-Reports/HowTo/Offene-DNS-Resolver/Offene-DNS-Resolver.html>
if [[ $DOMAIN == "int.de" ]]; then
    ufw allow 53
fi

# Add these subdomains to samba dns server:
# .la .cloud .office .portal .chat .meet, .element, .matrix
samba-tool dns add la.$DOMAIN $SHORTEND_DOMAIN la A $IP -U administrator%$ADMIN_PASSWORD
samba-tool dns add la.$SHORTEND_DOMAIN $SHORTEND_DOMAIN la A $IP -U administrator%$ADMIN_PASSWORD

# We take here the normal Domain as the zone because it is only important for us to use these subdomains for the dns server if we are running this in local network (int.de)
# -> So in local network the domain and shotend_domain are the same
if [[ $DOMAIN == $SHORTEND_DOMAIN ]]; then
    samba-tool dns add la.$DOMAIN $DOMAIN cloud A $IP -U administrator%$ADMIN_PASSWORD
    samba-tool dns add la.$DOMAIN $DOMAIN office A $IP -U administrator%$ADMIN_PASSWORD
    samba-tool dns add la.$DOMAIN $DOMAIN portal A $IP -U administrator%$ADMIN_PASSWORD
    samba-tool dns add la.$DOMAIN $DOMAIN chat A $IP -U administrator%$ADMIN_PASSWORD
    samba-tool dns add la.$DOMAIN $DOMAIN meet A $IP -U administrator%$ADMIN_PASSWORD
    samba-tool dns add la.$DOMAIN $DOMAIN element A $IP -U administrator%$ADMIN_PASSWORD
    samba-tool dns add la.$DOMAIN $DOMAIN matrix A $IP -U administrator%$ADMIN_PASSWORD
fi

# Add all these entries to /etc/hosts
if ! grep -q "cloud.$DOMAIN" /etc/hosts; then
    echo "$IP cloud.$DOMAIN" >> /etc/hosts # Nextcloud
    echo "$IP office.$DOMAIN" >> /etc/hosts # Online Office
    echo "$IP portal.$DOMAIN" >> /etc/hosts # Libre Workspace Portal
    echo "$IP meet.$DOMAIN" >> /etc/hosts # Jitsi Meet
    echo "$IP element.$DOMAIN" >> /etc/hosts # Element
    echo "$IP matrix.$DOMAIN" >> /etc/hosts # Matrix
    echo "$IP $DOMAIN" >> /etc/hosts # Domain itself
fi


# Insert 
# interfaces = 127.0.0.1 $IP
# bind interfaces only = yes
# to /etc/samba/smb.conf in the [global] section
# (Because otherwise samba-ad-dc would also listen on the docker0 interface)
sed -i "/^\[global\]/a interfaces = 127.0.0.1 $IP" /etc/samba/smb.conf
sed -i "/^\[global\]/a bind interfaces only = yes" /etc/samba/smb.conf

# Update cfg file:
# Remove the lines with "AUTH_LDAP" in it
sed -i "/AUTH_LDAP/d" /etc/libre-workspace/portal/portal.conf

# Add the Samba AD settings to the cfg file
# Ensure that we put in a new line
echo "" >> /etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_SERVER_URI=\"ldaps://localhost\"" >>/etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_DC=\"$LDAP_DC\"" >>/etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_BIND_DN=\"cn=Administrator,cn=users,$LDAP_DC\"" >>/etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_BIND_PASSWORD='$ADMIN_PASSWORD'" >>/etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_USER_DN_TEMPLATE=\"cn=%(user)s,cn=users,$LDAP_DC\"" >>/etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_GROUP_SEARCH_BASE=\"cn=Groups,$LDAP_DC\"" >>/etc/libre-workspace/portal/portal.conf
echo "export AUTH_LDAP_GROUP_ADMIN_DN=\"CN=Administrators,CN=Builtin,$LDAP_DC\"" >>/etc/libre-workspace/portal/portal.conf

# Mark samba_dc installed
ln -s /etc/samba /root/samba_dc

systemctl enable --now samba-ad-dc
systemctl restart samba-ad-dc
# Restart Libre Worksapce Services if the installation_running file is not present, so we are not in the middle of another installation
if [ ! -f /var/lib/libre-workspace/portal/installation_running ]; then
    systemctl restart libre-workspace-service.service
    systemctl restart libre-workspace-portal.service
fi
