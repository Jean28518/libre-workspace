#!/bin/bash

# This script is started if the user logs in.

# Check if this script already ran
if [ -f $HOME/.setup_desktop ]; then
    exit
fi

# Because otherwise the gsettings are not yet available
sleep 10

# We are in a cinnamon desktop environment

# Set the background image
gsettings set org.cinnamon.desktop.background picture-uri "file:///usr/lib/libre-workspace/portal/lac/static/lac/images/desktop_remote.jpg"

# Set icon theme to yaru-blue
gsettings set org.cinnamon.desktop.interface icon-theme "Yaru-blue"
# Set cursor theme to yaru
gsettings set org.cinnamon.desktop.interface cursor-theme "Yaru"
# Set gtk theme to yaru
gsettings set org.cinnamon.desktop.interface gtk-theme "Yaru-blue"
# Set cinnamon theme to arc-dark
gsettings set org.cinnamon.theme name "Arc-Dark"

# Disable sound applet in the panel
gsettings set org.cinnamon enabled-applets "['panel1:left:0:menu@cinnamon.org:0', 'panel1:left:1:separator@cinnamon.org:1', 'panel1:left:2:grouped-window-list@cinnamon.org:2', 'panel1:right:9:keyboard@cinnamon.org:8', 'panel1:right:10:favorites@cinnamon.org:9', 'panel1:right:13:power@cinnamon.org:12', 'panel1:right:14:calendar@cinnamon.org:13', 'panel1:right:15:cornerbar@cinnamon.org:14', 'panel1:right:3:xapp-status@cinnamon.org:15', 'panel1:right:2:notifications@cinnamon.org:16', 'panel1:right:1:systray@cinnamon.org:17', 'panel1:right:0:network@cinnamon.org:18']"

# Remove terminal from the grouped window list
# TODO

# Disable logout prompt
gsettings set org.cinnamon.SessionManager logout-prompt false
# Enable auto-save-session
gsettings set org.cinnamon.SessionManager auto-save-session true

# Set bottom-notifications to true
gsettings set org.cinnamon.desktop.notifications bottom-notifications true

# Disable effects
gsettings set org.cinnamon desktop-effects false
gsettings set org.cinnamon desktop-effects-workspace false

# Disable Shadows under windows
if ! grep -q "export MUFFIN_NO_SHADOWS=1;" $HOME/.profile; then
    echo "export MUFFIN_NO_SHADOWS=1;" >> $HOME/.profile
fi

touch $HOME/.setup_desktop