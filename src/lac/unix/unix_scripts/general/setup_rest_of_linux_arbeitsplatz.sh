# You need to run this script as root.
# DOMAIN
# ADMIN_PASSWORD
# IP
# LDAP_DC


DEBIAN_FRONTEND=noninteractive

# Remove the the block which begins with "# SED-LOCALHOST-ENTRY" and is 10 lines long
sed -i "/# SED-LOCALHOST-ENTRY/,+10d" /etc/caddy/Caddyfile

# CADDYFILE:

# If we have set $CUSTOM_ACCESS
if [ -n "$CUSTOM_ACCESS" ] ; then
  # Change the linux arbeits zentrale to the finished domain to $CUSTOM_ACCESS
  sed -i "s/:443 :23816/$CUSTOM_ACCESS/g" /etc/caddy/Caddyfile
  # Remove the line from tls internal { and the two lines after it if $CUSTOM_ACCESS is not :23816
  #  tls internal {
  #     on_demand
  # }
  if [ $CUSTOM_ACCESS != ":23816" ] ; then
    sed -i "/    tls internal {/,+2d" /etc/caddy/Caddyfile
  fi

  if [ $CUSTOM_ACCESS = ":23816" ] ; then
    # If we have set $CUSTOM_ACCESS to :23816, we need to open the port 23816
    ufw allow 23816
  fi
else
  # Otherwise we need to:
  # - Add access page reverse proxy on ip address
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

  # - Enable tls internal if domain is int.de
  if [ $DOMAIN = "int.de" ] ; then
    sed -i "s/#tls internal/tls internal/g" /etc/caddy/Caddyfile
  fi
  # - Set the correct domain in the caddyfile
  sed -i "s/SED_DOMAIN/$DOMAIN/g" /etc/caddy/Caddyfile
  # - Set the correct domain for the portal in the caddyfile
  sed -i "s/:443 :23816/portal.$DOMAIN/g" /etc/caddy/Caddyfile 
  # Remove the line from tls internal { and the two lines after it if domain is not int.de:
  #  tls internal {
  #     on_demand
  # }
  if [ $DOMAIN != "int.de" ] ; then
    sed -i "/    tls internal {/,+2d" /etc/caddy/Caddyfile
  fi
fi

# END CADDYFILE


systemctl reload caddy

# Set the cfg file of lac:
# LINUX_ARBEITSPLATZ_CONFIGURED=False to LINUX_ARBEITSPLATZ_CONFIGURED=True
sed -i "s/LINUX_ARBEITSPLATZ_CONFIGURED=False/LINUX_ARBEITSPLATZ_CONFIGURED=True/g" /usr/share/linux-arbeitsplatz/cfg

# Remove the lines with "EMAIL" in it
sed -i "/EMAIL/d" /usr/share/linux-arbeitsplatz/cfg

# Enable the unix service
/usr/bin/systemctl enable linux-arbeitsplatz-unix.service

rm installation_running

# After everything is configured, we need to restart the whole server
reboot
