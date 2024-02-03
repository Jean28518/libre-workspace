# This will be removed in the setup_rest_of_linux_arbeitsplatz.sh script.

LW_SCRIPTS=$(pwd)

touch installation_running

# This script installs the whole linux-arbeitsplatz how defined in the environment variables.
cd $LW_SCRIPTS/../general
. basics.sh

# Install SAMBA DC
cd $LW_SCRIPTS/../general
. setup_samba_dc.sh

# If the environment variable NEXTCLOUD is not empty
if [ ! -z "$NEXTCLOUD" ]; then
    # Install Nextcloud
    cd $LW_SCRIPTS/../nextcloud
    . setup_nextcloud.sh
fi

# If the environment variable COLLABORA is not empty
if [ ! -z "$COLLABORA" ]; then
    # Install Collabora
    cd $LW_SCRIPTS/../collabora
    . setup_collabora.sh
fi

# If the environment variable ONLYOFFICE is not empty
if [ ! -z "$ONLYOFFICE" ]; then
    # Install Onlyoffice
    cd $LW_SCRIPTS/../onlyoffice
    . setup_onlyoffice.sh
fi

# If the environment variable ROCKETCHAT is not empty
if [ ! -z "$ROCKETCHAT" ]; then
    # Install Rocket.Chat
    cd $LW_SCRIPTS/../rocketchat
    . setup_rocketchat.sh
fi

# If the environment variable ROCKETCHAT is not empty
if [ ! -z "$MATRIX" ]; then
    # Install Matrix
    cd $LW_SCRIPTS/../matrix
    . setup_matrix.sh
fi

# If the environment variable JITSI is not empty
if [ ! -z "$JITSI" ]; then
    # Install Jitsi
    cd $LW_SCRIPTS/../jitsi
    . setup_jitsi.sh
fi

# Distribute the certificates for local installations
if [ $DOMAIN = "int.de" ] ; then
    cd $LW_SCRIPTS/../general
    . setup_internal_https.sh
fi

# Install the rest of the linux-arbeitsplatz
cd $LW_SCRIPTS/../general
. setup_rest_of_linux_arbeitsplatz.sh