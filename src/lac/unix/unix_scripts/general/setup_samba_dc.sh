# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD
# LDAP_DC
# SHORTEND_DOMAIN (We need this for the samba dns server)

export DEBIAN_FRONTEND=noninteractive

## Setup DNS-Environment ##################################
hostnamectl set-hostname la
echo "$IP la.$DOMAIN la.$SHORTEND_DOMAIN la" >> /etc/hosts # IP of the server itself

# For ubuntu systems
systemctl disable --now systemd-resolved

# Make sure we don't have dnsmasq installed
sudo apt purge dnsmasq -y

# Prepare resolv.conf
chattr -i -a /etc/resolv.conf
rm -f /etc/resolv.conf
touch /etc/resolv.conf
echo "nameserver $IP" >> /etc/resolv.conf # This is the IP of the server itself. Needed for docker containers e.g.
echo "nameserver 208.67.222.222" >> /etc/resolv.conf # OpenDNS
chattr +i +a /etc/resolv.conf

## Setup SAMBA DC #########################################

# We need to set this variables that the krb5-config package does not ask for them
export REALM=$SHORTEND_DOMAIN
export KDC=la.$DOMAIN
export ADMIN_SERVER=la.$DOMAIN
apt update 
apt install -y acl attr samba samba-dsdb-modules samba-vfs-modules smbclient winbind libpam-winbind libnss-winbind libpam-krb5 krb5-config krb5-user dnsutils chrony net-tools samba-ad-provision

systemctl disable --now smbd nmbd winbind
systemctl unmask samba-ad-dc
systemctl enable samba-ad-dc

mv /etc/samba/smb.conf /etc/samba/smb.conf.bak
# Wee need to set this variables that the samba config script does not ask for them
# Host-Role
export SAMBA_HOST_ROLE=dc
# DNS Backend
export SAMBA_DNS_BACKEND=SAMBA_INTERNAL
# DNS Forwarder (OpenDNS)
export SAMBA_DNS_FORWARDER=$IP
# Administrator password
export SAMBA_ADMIN_PASSWORD=$ADMIN_PASSWORD

samba-tool domain provision --realm=$SHORTEND_DOMAIN --domain=la.$SHORTEND_DOMAIN --adminpass=$ADMIN_PASSWORD

mv /etc/krb5.conf /etc/krb5.conf.orig
cp /var/lib/samba/private/krb5.conf /etc/krb5.conf

systemctl start samba-ad-dc


# Configuration for the password policy
samba-tool domain passwordsettings set --complexity=off
samba-tool domain passwordsettings set --history-length=0
samba-tool domain passwordsettings set --min-pwd-age=0
samba-tool domain passwordsettings set --max-pwd-age=0


# Enable LDAPS:
cd /etc/samba/tls/

subj="
C=DE
ST=BV
O=Nbg
localityName=Nuremberg
commonName=$DOMAIN
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
echo "dns forwarder = 208.67.222.222" >> /etc/samba/smb.conf
echo "tls enabled  = yes" >> /etc/samba/smb.conf
echo "tls keyfile  = /etc/samba/tls/myKey.pem" >> /etc/samba/smb.conf
echo "tls certfile = /etc/samba/tls/myCert.pem" >> /etc/samba/smb.conf
echo "tls cafile   =" >> /etc/samba/smb.conf

# Restart samba
systemctl restart samba-ad-dc

# Allow ldaps in the firewall
ufw allow ldaps
# Allow DNS in the firewall
ufw allow 53
# Allow 88 and 464 for kerberos
ufw allow 88
ufw allow 464
# Allow 139 and 445 for samba
ufw allow 139
ufw allow 445


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
echo "$IP cloud.$DOMAIN" >> /etc/hosts # Nextcloud
echo "$IP office.$DOMAIN" >> /etc/hosts # Online Office
echo "$IP portal.$DOMAIN" >> /etc/hosts # Linux-Arbeitsplatz Central
echo "$IP meet.$DOMAIN" >> /etc/hosts # Jitsi Meet
echo "$IP element.$DOMAIN" >> /etc/hosts # Element
echo "$IP matrix.$DOMAIN" >> /etc/hosts # Matrix
echo "$IP $DOMAIN" >> /etc/hosts # Domain itself