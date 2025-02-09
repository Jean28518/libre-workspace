#!/bin/bash

# This script should be run as root
# We need this variables:
# DOMAIN
# IP
# ADMIN_PASSWORD

. guacamole_version.sh

# Install Cinnamon, Xrdp and recommended software
export DEBIAN_FRONTEND=noninteractive
sudo apt install task-cinnamon-desktop cinnamon-l10n xrdp chromium yaru-theme-icon yaru-theme-gtk arc-theme libreoffice-l10n-de hunspell hunspell-de-de hyphen-de remmina keepassxc remmina-plugin-rdp remmina-plugin-vnc gimp inkscape flameshot gnome-calendar filezilla pdfarranger xournalpp gdebi -y
wget https://github.com/Jean28518/linux-assistant/releases/latest/download/linux-assistant.deb
sudo apt install ./linux-assistant.deb -y
rm linux-assistant.deb

# Install Guacamole as docker container
mkdir -p /root/desktop
cp docker-compose.yml /root/desktop/docker-compose.yml

sed -i "s/SED_GUACAMOLE_VERSION/$GUACAMOLE_VERSION/g" /root/desktop/docker-compose.yml

CLIENT_ID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
CLIENT_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
# Add the oidc client to the oidc provider
cd /usr/share/linux-arbeitsplatz/
bash django_add_oidc_provider_client.sh "Guacamole" "$CLIENT_ID" "$CLIENT_SECRET" "https://desktop.$DOMAIN/guacamole"
cd -

# OpenID Connect:
sed -i "s/SED_OPENID_AUTHORIZATION_ENDPOINT/https:\/\/portal.$DOMAIN\/openid\/authorize/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_JWKS_ENDPOINT/https:\/\/portal.$DOMAIN\/openid\/jwks/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_ISSUER/https:\/\/portal.$DOMAIN\/openid/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_CLIENT_ID/$CLIENT_ID/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_REDIRECT_URI/https:\/\/desktop.$DOMAIN\/guacamole/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_USERNAME_CLAIM_TYPE/preferred_username/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_GROUPS_CLAIM_TYPE/groups/g" /root/desktop/docker-compose.yml
sed -i "s/SED_OPENID_MAX_TOKEN_VALIDITY/200/g" /root/desktop/docker-compose.yml

docker run --rm guacamole/guacamole:$GUACAMOLE_VERSION /opt/guacamole/bin/initdb.sh --mysql > /root/desktop/initdb.sql
docker-compose -f /root/desktop/docker-compose.yml up -d
docker cp /root/desktop/initdb.sql desktop_mysql_1:/initdb.sql
docker exec -it desktop_mysql_1 bash -c "mysql -u root -pFei1woo9 guacamole < /initdb.sql"



echo "desktop.$DOMAIN" >> /etc/hosts
samba-tool dns add la.$DOMAIN $DOMAIN desktop A $IP -Uadministrator%$ADMIN_PASSWORD

echo "
desktop.$DOMAIN {
  #tls internal
  redir / /guacamole/ 301
  reverse_proxy localhost:28925
}
" >> /etc/caddy/Caddyfile

systemctl reload caddy

chmod 600 /usr/share/linux-arbeitsplatz/cfg
chmod 700 /usr/share/linux-arbeitsplatz/unix

ufw allow from 192.168.0.0/16 to any port 3389

# In the next step we have to configure this linux server unix logins and we have to set these passwords into the guacamole database that we generate a connection to this linux server automatically for every user logging in.

# We get all users through the samba-tool command
USERS=$(samba-tool user list --full-dn)
# We only need the usernames:
for USER in $USERS; do
    USERNAME=$(echo $USER | cut -d'=' -f2 | cut -d',' -f1)

    # We ignore "Guest" and "krbtgt"
    if [ "$USERNAME" == "Guest" ] || [ "$USERNAME" == "krbtgt" ]; then
        continue
    fi

    # Check if the user has administrator rights
    if samba-tool group listmembers "Domain Admins" | grep -q $USERNAME; then
        ADMINISTRATOR="1"
    else
        ADMINISTRATOR="0"
    fi

    # The second argument is the password. We set it to an empty string because its then generated automatically.
    bash /usr/share/linux-arbeitsplatz/unix/unix_scripts/desktop/add_user.sh "$USERNAME" "" "$ADMINISTRATOR"
    echo "$USERNAME"   
done


# If user systemv exists on linux we need to add him into autologin in lightdm
if [ -d "/home/systemv" ]; then
    echo "[Seat:*]
autologin-user=systemv
autologin-user-timeout=0" > /etc/lightdm/lightdm.conf
fi
