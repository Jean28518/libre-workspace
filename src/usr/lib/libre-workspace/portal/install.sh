# This script is called directly after the installation of the .deb package
# It is used to setup the django application and the caddy server

sudo mkdir -p /var/www/libre-workspace-static/
sudo chmod -R 777 /var/www/libre-workspace-static/

cp /etc/libre-workspace/portal/portal.conf.example /etc/libre-workspace/portal/portal.conf

mkdir -p /var/lib/libre-workspace/portal/
cd /var/lib/libre-workspace/portal/
python3 -m venv venv
cd -

ln -s /usr/bin/python3 /usr/bin/python

source /var/lib/libre-workspace/portal/venv/bin/activate
pip install --upgrade pip
pip install -r /usr/lib/libre-workspace/portal/requirements.txt 
# Make sure that the database is up to date (sometimes e.g. oidc_provider needs to be updated)
cd /usr/lib/libre-workspace/portal/
python3 manage.py makemigrations --no-input
python manage.py migrate --no-input

# Get the current IP-Adress
# Get the output of hostname -I and cut the first part of it
IP=`hostname -I | cut -d' ' -f1`

# If caddy file does not has # PORTAL-ENTRY, then add it
if ! grep -q "# PORTAL-ENTRY" /etc/caddy/Caddyfile; then

# Remove :80 entry from caddy file, because we don't want to use it
libre-workspace-remove-webserver-entry :80

echo "# PORTAL-ENTRY
:443 {
    tls internal {
        on_demand
    }
    handle_path /static* {
        root * /var/www/libre-workspace-static
        file_server
        encode zstd gzip
    }
    handle_path /media* {
        root * /var/lib/libre-workspace/portal/media
        file_server
        encode zstd gzip
    }
    reverse_proxy localhost:11123
}

# SED-LOCALHOST-ENTRY
# We need this one for the local browser to work
# Only http, because we don't want a warning about the self-signed certificate
http://localhost {
    reverse_proxy https://localhost:443 {
        transport http {
            tls_insecure_skip_verify
        }
    }
}

" >> /etc/caddy/Caddyfile

# If something is running on port 80, then systemctl restart caddy will silently hang
systemctl restart caddy

fi