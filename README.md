# Linux-Arbeitsplatz Zentrale

WIP

## How to develop

```bash
sudo apt-get install libldap2-dev python3-venv libsasl2-dev
cd src
python3 -m venv .env
source .env/bin/activate
pip install django python-ldap django-auth-ldap
python manage.py runserver

deactivate
```
