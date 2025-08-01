# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP
# LDAP_DC
# LANGUAGE_CODE


DEBIAN_FRONTEND=noninteractive

# Remove the the block which begins with "# SED-LOCALHOST-ENTRY" and is 10 lines long
sed -i "/# SED-LOCALHOST-ENTRY/,+10d" /etc/caddy/Caddyfile

# CADDYFILE:

# If we have set $CUSTOM_ACCESS
if [ -n "$CUSTOM_ACCESS" ] ; then


  # Change the linux arbeits zentrale to the finished domain to $CUSTOM_ACCESS and set the allowed hosts properly
  if [ $CUSTOM_ACCESS = ":23816" ] ; then
    sed -i "s/:443/https:\/\/$IP:23816/g" /etc/caddy/Caddyfile
    # Insert the line with tls internal after the line with :23816
    sed -i "/https:\/\/$IP:23816/a \    tls internal" /etc/caddy/Caddyfile
    echo "export ALLOWED_HOSTS=\"$IP:23816\"" >> /etc/libre-workspace/portal/portal.conf
  else
    sed -i "s/:443/$CUSTOM_ACCESS/g" /etc/caddy/Caddyfile

    # Get the CUSTOM_ACCESS without : extension if it is e.g. my.domain.com:23816
    CUSTOM_ACCESS_DOMAIN=$(echo $CUSTOM_ACCESS | cut -d ":" -f 1)
    echo "export ALLOWED_HOSTS=\"$CUSTOM_ACCESS_DOMAIN\"" >> /etc/libre-workspace/portal/portal.conf
  fi

  # Remove the line from tls internal { and the two lines after it if $CUSTOM_ACCESS is not :23816
  #  tls internal {
  #     on_demand
  # }
  sed -i "/    tls internal {/,+2d" /etc/caddy/Caddyfile

  # Check if :23816 is in $CUSTOM_ACCESS
  if [[ $CUSTOM_ACCESS == *":23816"* ]] ; then
    # If we have set $CUSTOM_ACCESS to :23816, we need to open the port 23816
    ufw allow 23816
  fi

  # Set the password for the local admin user (django)
  # Set INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP in /etc/libre-workspace/portal/portal.conf
  sed -i "s/INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP=.*/INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP=$ADMIN_PASSWORD/g" /etc/libre-workspace/portal/portal.conf
  # Set the Password for the admin user via script
  libre-workspace-set-local-admin-password "$ADMIN_PASSWORD"

else
  # Otherwise we need to:
  # - Add access page reverse proxy on ip address
  echo "$IP http://localhost {
      #tls internal
      handle_path /static* {
          root * /var/www/libre-workspace-static
          file_server
          encode zstd gzip
      } 
      handle {
      rewrite * /welcome/access
      reverse_proxy localhost:11123
      }
  }

  " >> /etc/caddy/Caddyfile

  # - Enable tls internal if domain is int.de
  if [ $DOMAIN = "int.de" ] ; then
    sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
  fi
  # - Set the correct domain in the caddyfile
  sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile
  # - Set the correct domain for the portal in the caddyfile
  sed -i "s/:443/portal.$DOMAIN/g" /etc/caddy/Caddyfile 
  # Remove the line from tls internal { and the two lines after it if domain is not int.de:
  #  tls internal {
  #     on_demand
  # }
  if [ $DOMAIN != "int.de" ] ; then
    sed -i "/    tls internal {/,+2d" /etc/caddy/Caddyfile
  fi
fi

# END CADDYFILE


systemctl restart caddy

# Set the cfg file of lac:
# LINUX_ARBEITSPLATZ_CONFIGURED=False to LINUX_ARBEITSPLATZ_CONFIGURED=True
sed -i "s/LINUX_ARBEITSPLATZ_CONFIGURED=False/LINUX_ARBEITSPLATZ_CONFIGURED=True/g" /etc/libre-workspace/portal/portal.conf

# Remove the lines with "EMAIL" in it
sed -i "/EMAIL/d" /etc/libre-workspace/portal/portal.conf

# Set the LANGUAGE_CODE in the portal.conf
sed -i "s/LANGUAGE_CODE=.*/LANGUAGE_CODE=$LANGUAGE_CODE/g" /etc/libre-workspace/portal/portal.conf

# Enable the unix service
/usr/bin/systemctl enable libre-workspace-service.service

# Create history folder:
mkdir -p /var/lib/libre-workspace/portal/history

# Make /etc/libre-workspace/ only readable for owner
chmod 700 /etc/libre-workspace/

rm /var/lib/libre-workspace/portal/installation_running

# After everything is configured, we need to restart the whole server
reboot
