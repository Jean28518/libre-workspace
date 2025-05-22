#!/bin/bash

# read cfg file:
if [ -f "src/etc/libre-workspace/portal/portal.conf" ]; then
    source src/etc/libre-workspace/portal/portal.conf
fi


source src/var/lib/libre-workspace/portal/venv/bin/activate

pip install -r src/usr/lib/libre-workspace/portal/requirements.txt


if [ -d "src/usr/lib/libre-workspace/portal" ]; then
    cd src/usr/lib/libre-workspace/portal
fi

python manage.py makemigrations
python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input
python manage.py creatersakey

echo "Starting server..."
python3 manage.py runserver localhost:8000
