# This will be removed in the setup_rest_of_linux_arbeitsplatz.sh script.
touch installation_running

# This script installs the whole linux-arbeitsplatz how defined in the environment variables.
. basics.sh

# Install SAMBA DC
. setup_samba_dc.sh

# If the environment variable NEXTCLOUD is not empty
if [ ! -z "$NEXTCLOUD" ]; then
    # Install Nextcloud
    cd ../nextcloud
    . setup_nextcloud.sh
    cd -
fi

# If the environment variable COLLABORA is not empty
if [ ! -z "$COLLABORA" ]; then
    # Install Collabora
    cd ../collabora
    . setup_collabora.sh
    cd -
fi

# If the environment variable ONLYOFFICE is not empty
if [ ! -z "$ONLYOFFICE" ]; then
    # Install Onlyoffice
    cd ../onlyoffice
    . setup_onlyoffice.sh
    cd -
fi

# If the environment variable ROCKETCHAT is not empty
if [ ! -z "$ROCKETCHAT" ]; then
    # Install Rocket.Chat
    cd ../rocketchat
    . setup_rocketchat.sh
    cd -
fi

# If the environment variable ROCKETCHAT is not empty
if [ ! -z "$MATRIX" ]; then
    # Install Matrix
    cd ../matrix
    . setup_matrix.sh
    cd -
fi

# If the environment variable JITSI is not empty
if [ ! -z "$JITSI" ]; then
    # Install Jitsi
    cd ../jitsi
    . setup_jitsi.sh
    cd -
fi

# Distribute the certificates for local installations
if [ $DOMAIN = "int.de" ] ; then
    . setup_internal_https.sh
fi

# Install the rest of the linux-arbeitsplatz
. setup_rest_of_linux_arbeitsplatz.sh