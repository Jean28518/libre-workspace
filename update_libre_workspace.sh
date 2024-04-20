
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