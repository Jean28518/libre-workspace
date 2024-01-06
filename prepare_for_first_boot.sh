# This script is run once at first boot of the fresh installed system.

# Configure automatic login for user "systemv"
sed -i "s/^#autologin-user=.*/autologin-user=systemv/" "/etc/lightdm/lightdm.conf"
sed -i "s/^#autologin-user-timeout=.*/autologin-user-timeout=0/" "/etc/lightdm/lightdm.conf"


# Add autostart file for the openbox desktop environment
cp /usr/share/linux-arbeitsplatz/openbox-autostart /etc/xdg/openbox/autostart