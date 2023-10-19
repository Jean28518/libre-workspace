# Linux-Arbeitsplatz Zentrale

Using Samba as domain controller.

## How to deploy

```bash
# Make sure you have AD domain controler like samba active and ldaps enabled.

wget https://github.com/Jean28518/linux-arbeitsplatz-central/releases/tag/v0.1.0
sudo apt install ./linux-arbeitsplatz.deb

vim /usr/share/linux-arbeitsplatz/cfg
# Adjust all variables

systemctl enable linux-arbeitsplatz-web --now
systemctl enable linux-arbeitsplatz-unix --now
systemctl restart linux-arbeitsplatz-web
```

## Caddyfile

```Caddyfile
central.int.de {
  handle_path /static* {
        root * /var/www/linux-arbeitsplatz-static
        file_server
        encode zstd gzip
  }
  reverse_proxy localhost:11123
}
```

## How to develop

Copy the content of env.example into your ~/.bashrc file and adjust it to your needs. Restart the terminal.

```bash
sudo apt-get install libldap2-dev python3-venv libsasl2-dev
cd src/lac/
python3 -m venv .env

source .env/bin/activate
pip install django python-ldap django-auth-ldap
python manage.py migrate

python manage.py runserver

deactivate
```
