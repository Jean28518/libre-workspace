# Get current installed version of Libre Workspace
INSTALLED_VERSION=$(dpkg -s libre-workspace-portal | grep Version | cut -d " " -f 2)

# Get latest version of Libre Workspace from GitHub
LATEST_VERSION=$(curl -s https://api.github.com/repos/Jean28518/libre-workspace/releases/latest | grep tag_name | cut -d '"' -f 4)

# If the installed version is the same as the latest version, then exit
if [ "v$INSTALLED_VERSION" == "$LATEST_VERSION" ]; then
    echo "Libre Workspace is already up to date. Exiting..."
    exit 0
fi

wget https://github.com/Jean28518/libre-workspace/releases/latest/download/libre-workspace-portal.deb

# If libre-workspace.deb is not a file, then exit
if [ ! -f "libre-workspace-portal.deb" ]; then
    echo "libre-workspace-portal.deb file not found. Canceling Libre Workspace Update..."
    exit 1
fi

apt-get install ./libre-workspace-portal.deb -y
rm libre-workspace-portal.deb

# Update all pip packages
if [ -d "/var/lib/libre-workspace/portal/venv/bin" ]; then
    source /var/lib/libre-workspace/portal/venv/bin/activate
else
    
fi
pip install --upgrade pip
pip install --upgrade -r /usr/lib/libre-workspace/portal/requirements.txt


# Make sure, both services are enabled and running
systemctl enable libre-workspace-service
systemctl enable libre-workspace-portal
systemctl restart libre-workspace-service
systemctl restart libre-workspace-portal