# This will be removed in the setup_rest_of_linux_arbeitsplatz.sh script.
touch installation_running

# This script installs the whole linux-arbeitsplatz how defined in the environment variables.
. basics.sh

# Install SAMBA DC
. setup_samba_dc.sh

# If the environment variable NEXTCLOUD is not empty
if [ ! -z "$NEXTCLOUD" ]; then
    # Install Nextcloud
    . setup_nextcloud.sh
fi

# If the environment variable COLLABORA is not empty
if [ ! -z "$COLLABORA" ]; then
    # Install Collabora
    . setup_collabora.sh
fi

# If the environment variable ONLYOFFICE is not empty
if [ ! -z "$ONLYOFFICE" ]; then
    # Install Onlyoffice
    . setup_onlyoffice.sh
fi

# If the environment variable ROCKETCHAT is not empty
if [ ! -z "$ROCKETCHAT" ]; then
    # Install Rocket.Chat
    . setup_rocketchat.sh
fi

# If the environment variable JITSI is not empty
if [ ! -z "$JITSI" ]; then
    # Install Jitsi
    . setup_jitsi.sh
fi

# Distribute the certificates for local installations
if [ $DOMAIN = "int.de" ] ; then
    . setup_internal_https.sh
fi

# Install the rest of the linux-arbeitsplatz
. setup_rest_of_linux_arbeitsplatz.sh