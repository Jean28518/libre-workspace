# This script is called directly after the installation of the .deb package
# It is used to setup the django application and the caddy server

sudo mkdir -p /var/www/linux-arbeitsplatz-static/
sudo chmod -R 777 /var/www/linux-arbeitsplatz-static/

if [ ! -d "/usr/share/linux-arbeitsplatz" ]; then
    cd src/lac/
else 
    cd /usr/share/linux-arbeitsplatz/
fi

if [ ! -f "cfg" ]; then
    cp cfg.example cfg
fi

python3 -m venv .env

ln -s /usr/bin/python3 /usr/bin/python

source .env/bin/activate
pip install django python-ldap django-auth-ldap gunicorn
python manage.py migrate --no-input

# Get the current IP-Adress
# Get the output of hostname -I and cut the first part of it
IP=`hostname -I | cut -d' ' -f1`

echo ":443 {
    tls internal {
        on_demand
    }
    handle_path /static* {
        root * /var/www/linux-arbeitsplatz-static
        file_server
        encode zstd gzip
    }
    reverse_proxy localhost:11123
}


# We need this one for the local browser to work
# Only http, because we don't want a warning about the self-signed certificate
http://localhost {
    reverse_proxy https://127.0.0.1:443 {
        transport http {
            tls_insecure_skip_verify
        }
    }
}

" >> /etc/caddy/Caddyfile