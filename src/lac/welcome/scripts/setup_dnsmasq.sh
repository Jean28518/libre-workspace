# CURRENTLY WE ARE NOT USING THIS BECAUSE DNSMASQ AND SAMBA DC ARE NOT WORKING TOGETHER AT THE MOMENT
# (We are using the dns server of samaba dc)

# This script should be run as root
# We need this variables:
# DOMAIN
# IP

# Disable internal DNS and install dnsmasq

export DEBIAN_FRONTEND=noninteractive

systemctl disable --now systemd-resolved
unlink /etc/resolv.conf

apt install dnsmasq -y

rm -f /etc/resolv.conf

touch /etc/resolv.conf

echo "nameserver 127.0.0.1" >> /etc/resolv.conf 
echo "nameserver $IP" >> /etc/resolv.conf # This is the IP of the server itself. Needed for docker containers e.g.
echo "nameserver 208.67.222.222" >> /etc/resolv.conf # OpenDNS

# Make /etc/resolv.conf immutable because the system sometimes overwrites it.
chattr +i /etc/resolv.conf

# Append to /etc/dnsmasq.conf:
echo "listen-address=127.0.0.1" >> /etc/dnsmasq.conf
# echo "listen-address=$IP" >> /etc/dnsmasq.conf

# Append these subdomains to /etc/hosts: 
# .la .cloud .portal .central .chat .meet
echo "$IP la.$DOMAIN" >> /etc/hosts # Samba DC
echo "$IP cloud.$DOMAIN" >> /etc/hosts # Nextcloud
echo "$IP office.$DOMAIN" >> /etc/hosts # Online Office
echo "$IP portal.$DOMAIN" >> /etc/hosts # Linux-Arbeitsplatz Portal
echo "$IP central.$DOMAIN" >> /etc/hosts # Linux-Arbeitsplatz Central
echo "$IP chat.$DOMAIN" >> /etc/hosts # Rocket.Chat
echo "$IP meet.$DOMAIN" >> /etc/hosts # Jitsi Meet
echo "$IP $DOMAIN" >> /etc/hosts # Domain itself

# Finally switch the services
systemctl stop systemd-resolved.service
systemctl disable systemd-resolved.service

systemctl enable dnsmasq
systemctl restart dnsmasq
ufw allow 53

