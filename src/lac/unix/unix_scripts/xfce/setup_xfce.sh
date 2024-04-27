#!/bin/bash

apt-get purge lightdm-autologin-greeter openbox -y
apt-get install lightdm-gtk-greeter -y
apt-get install task-xfce-desktop -y

# Enable userlist for lightdm
sed -i "s/^#greeter-hide-users=.*/greeter-hide-users=false/" "/etc/lightdm/lightdm.conf"

# Set desktop background
rm /usr/share/images/desktop-base/default
ln -s /usr/share/linux-arbeitsplatz/lac/static/lac/images/desktop.jpg /usr/share/images/desktop-base/default