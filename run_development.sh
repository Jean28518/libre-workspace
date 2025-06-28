#!/bin/bash

# read cfg file:
if [ -f "/etc/libre-workspace/portal/portal.conf" ]; then
    source /etc/libre-workspace/portal/portal.conf
fi


source /var/lib/libre-workspace/portal/venv/bin/activate

pip install -r /usr/lib/libre-workspace/portal/requirements.txt


if [ -d "/usr/lib/libre-workspace/portal" ]; then
    cd /usr/lib/libre-workspace/portal
fi

python manage.py makemigrations
python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input
python manage.py creatersakey
python3 manage.py compilemessages


echo "Starting server..."
python3 manage.py runserver 0.0.0.0:8000
