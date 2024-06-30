# Get current installed version of Libre Workspace
INSTALLED_VERSION=$(dpkg -s linux-arbeitsplatz | grep Version | cut -d " " -f 2)

# Get latest version of Libre Workspace from GitHub
LATEST_VERSION=$(curl -s https://api.github.com/repos/Jean28518/libre-workspace/releases/latest | grep tag_name | cut -d '"' -f 4)

# If the installed version is the same as the latest version, then exit
if [ "v$INSTALLED_VERSION" == "$LATEST_VERSION" ]; then
    echo "Libre Workspace is already up to date. Exiting..."
    exit 0
fi

wget https://github.com/Jean28518/libre-workspace/releases/latest/download/linux-arbeitsplatz.deb

# If linux-arbeitsplatz.deb is not a file, then exit
if [ ! -f "linux-arbeitsplatz.deb" ]; then
    echo "linux-arbeitsplatz.deb file not found. Canceling Libre Workspace Update..."
    exit 1
fi

apt-get install ./linux-arbeitsplatz.deb -y
rm linux-arbeitsplatz.deb

# Update all pip packages
if [ -d "src/lac/" ]; then
    source src/lac/.env/bin/activate
elif [ -d "/usr/share/linux-arbeitsplatz/.env/bin" ]; then
    source /usr/share/linux-arbeitsplatz/.env/bin/activate
else
    source .env/bin/activate
fi
pip install --upgrade pip
pip install --upgrade -r requirements.txt


# Make sure, both services are enabled and running
systemctl enable linux-arbeitsplatz-unix
systemctl enable linux-arbeitsplatz-web
systemctl restart linux-arbeitsplatz-*