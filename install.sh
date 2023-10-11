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

source .env/bin/activate
pip install django python-ldap django-auth-ldap gunicorn
python manage.py migrate --no-input