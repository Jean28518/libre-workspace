# Linux-Arbeitsplatz Zentrale

Using Samba as domain controller.

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