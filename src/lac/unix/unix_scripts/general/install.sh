# This will be removed in the setup_rest_of_linux_arbeitsplatz.sh script.

LW_SCRIPTS=$(pwd)

touch installation_running
echo "Starting installation..."

# This script installs the whole linux-arbeitsplatz how defined in the environment variables.
cd $LW_SCRIPTS/../general
echo "Doing installations basics..."
. basics.sh

# Install SAMBA DC if the environment variable SAMBA_DC is not empty
if [ ! -z "$SAMBA_DC" ]; then
    echo "Doing samba dc installation..."
    # Install SAMBA DC
    cd $LW_SCRIPTS/../samba_dc
    . setup_samba_dc.sh
fi

# If the environment variable NEXTCLOUD is not empty
if [ ! -z "$NEXTCLOUD" ]; then
    echo "Nextcloud installation..."
    # Install Nextcloud
    cd $LW_SCRIPTS/../nextcloud
    . setup_nextcloud.sh
fi

# If the environment variable COLLABORA is not empty
if [ ! -z "$COLLABORA" ]; then
    echo "Collabora installation..."
    # Install Collabora
    cd $LW_SCRIPTS/../collabora
    . setup_collabora.sh
fi

# If the environment variable ONLYOFFICE is not empty
if [ ! -z "$ONLYOFFICE" ]; then
    echo "Onlyoffice installation..."
    # Install Onlyoffice
    cd $LW_SCRIPTS/../onlyoffice
    . setup_onlyoffice.sh
fi

# If the environment variable DESKTOP is not empty
if [ ! -z "$DESKTOP" ]; then
    echo "Desktop installation..."
    # Install Desktop
    cd $LW_SCRIPTS/../desktop
    . setup_desktop.sh
fi

# If the environment variable MATRIX is not empty
if [ ! -z "$MATRIX" ]; then
    echo "Matrix installation..."
    # Install Matrix
    cd $LW_SCRIPTS/../matrix
    . setup_matrix.sh
fi

# If the environment variable JITSI is not empty
if [ ! -z "$JITSI" ]; then
    echo "Jitsi installation..."
    # Install Jitsi
    cd $LW_SCRIPTS/../jitsi
    . setup_jitsi.sh
fi

# If the environment variable XFCE is not empty
if [ ! -z "$XFCE" ]; then
    echo "XFCE installation..."
    # Install XFCE
    cd $LW_SCRIPTS/../xfce
    . setup_xfce.sh
fi

# Distribute the certificates for local installations
if [ $DOMAIN = "int.de" ] ; then
    echo "Setting up internal https..."
    cd $LW_SCRIPTS/../general
    . setup_internal_https.sh
fi

# Install the rest of the linux-arbeitsplatz
echo "Setting up the rest of the linux-arbeitsplatz..."
cd $LW_SCRIPTS/../general
. setup_rest_of_linux_arbeitsplatz.sh