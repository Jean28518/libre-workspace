# This will be removed in the setup_rest_of_linux_arbeitsplatz.sh script.

touch /var/lib/libre-workspace/portal/installation_running
echo "Starting installation..."

# This script installs the whole libre-workspace how defined in the environment variables.
cd /usr/lib/libre-workspace/portal/unix/unix-scripts/general
echo "Doing installations basics..."
. basics.sh

# Install SAMBA DC if the environment variable SAMBA_DC is not empty
if [ ! -z "$SAMBA_DC" ]; then
    echo "Doing samba dc installation..."
    # Install SAMBA DC
    cd /usr/lib/libre-workspace/modules/samba_dc
    . setup_samba_dc.sh
fi

# Distribute the certificates for local installations
if [ $DOMAIN = "int.de" ] ; then
    echo "Setting up internal https..."
    cd /usr/lib/libre-workspace/portal/unix/unix-scripts/general
    . setup_internal_https.sh
fi

# If the environment variable NEXTCLOUD is not empty
if [ ! -z "$NEXTCLOUD" ]; then
    echo "Nextcloud installation..."
    # Install Nextcloud
    cd /usr/lib/libre-workspace/modules/nextcloud
    . setup_nextcloud.sh
fi

# If the environment variable COLLABORA is not empty
if [ ! -z "$COLLABORA" ]; then
    echo "Collabora installation..."
    # Install Collabora
    cd /usr/lib/libre-workspace/modules/collabora
    . setup_collabora.sh
fi

# If the environment variable ONLYOFFICE is not empty
if [ ! -z "$ONLYOFFICE" ]; then
    echo "Onlyoffice installation..."
    # Install Onlyoffice
    cd /usr/lib/libre-workspace/modules/onlyoffice
    . setup_onlyoffice.sh
fi

# If the environment variable DESKTOP is not empty
if [ ! -z "$DESKTOP" ]; then
    echo "Desktop installation..."
    # Install Desktop
    cd /usr/lib/libre-workspace/modules/desktop
    . setup_desktop.sh
fi

# If the environment variable MATRIX is not empty
if [ ! -z "$MATRIX" ]; then
    echo "Matrix installation..."
    # Install Matrix
    cd /usr/lib/libre-workspace/modules/matrix
    . setup_matrix.sh
fi

# If the environment variable JITSI is not empty
if [ ! -z "$JITSI" ]; then
    echo "Jitsi installation..."
    # Install Jitsi
    cd /usr/lib/libre-workspace/modules/jitsi
    . setup_jitsi.sh
fi

# If the environment variable XFCE is not empty
if [ ! -z "$XFCE" ]; then
    echo "XFCE installation..."
    # Install XFCE
    cd /usr/lib/libre-workspace/modules/xfce
    . setup_xfce.sh
fi

# Install the rest of the libre-workspace
echo "Setting up the rest of the libre-workspace..."
cd /usr/lib/libre-workspace/portal/unix/unix_scripts/general
. /usr/lib/libre-workspace/portal/unix/unix_scripts/general/setup_rest_of_libre-workspace.sh