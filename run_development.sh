#!/bin/bash

# read cfg file:
if [ -f "cfg" ]; then
    source cfg
fi

if [ -d "src/lac/" ]; then
    cd src/lac/
fi

source .env/bin/activate

pip install django python-ldap django-auth-ldap


python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input

echo "Starting server..."
python3 manage.py runserver
