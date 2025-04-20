#!/bin/bash

# Ensure that the dns server is set to the ip address of libre workspace (very important)

# You can start this script with two arguments:
# 1. The domain name of the realm. Example: int.de
# 2. The client name for joining the realm. Example: client1

# Get ip address of the server which will be used as dns server

# Get the domain name
# Is argument domain set?
if [ -z "$1" ] ; then
  DOMAIN=$(zenity --entry --title="Domain" --text="Please enter the domain name of the realm. Example: int.de")
else
    DOMAIN=$1
fi
export REALM=$(echo $DOMAIN | tr '[:lower:]' '[:upper:]')

# Get the client name for joining the realm
# Is argument client set?
if [ -z "$2" ] ; then
  CLIENT=$(zenity --entry --title="Client" --text="Please enter the client name for joining the realm. Example: client1")
else
    CLIENT=$2
fi

# Make sure time is synchronized
apt install chrony -y
chronyc makestep

apt-get update -y
apt-get install -y sssd-ad sssd-tools realmd adcli
echo "
[libdefaults]
    default_realm = $REALM
    dns_lookup_kdc = true  # Or false if KDCs are manually listed
    dns_lookup_realm = false # Or true
    rdns = false

[realms]
    $REALM = {
        kdc = la.$DOMAIN   # Replace with your actual KDC hostname(s) or IP(s)
        admin_server = la.$DOMAIN # Often the same as a KDC
    }

[domain_realm]
    .$DOMAIN = $REALM
    $DOMAIN = $REALM" > /etc/krb5.conf

apt-get install -y krb5-user sssd-krb5

hostnamectl set-hostname $CLIENT.$DOMAIN

systemctl restart sssd
echo "You need to enter the password of the realm administrator (libre workspace masterpassword):"
kinit administrator

# TODO: CHange IP to the IP of the client and adjust client name and also domain
samba-tool dns add la.int.de int.de client1 A 192.168.1.192 -U administrator

realm join -v -U administrator $DOMAIN

# Add activate mkhomedir with pam-auth-update
pam-auth-update --enable mkhomedir

# Hide the user list
echo "
[Seat:*]
greeter-show-manual-login=true
#greeter-hide-users=true" >> /etc/lightdm/lightdm.conf

echo "Please restart the system to apply the changes."