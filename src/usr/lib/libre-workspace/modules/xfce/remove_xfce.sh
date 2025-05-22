#!/bin/bash

apt-get purge task-xfce-desktop lightdm-gtk-greeter -y
apt-get install lightdm-autologin-greeter openbox -y

/sbin/reboot
