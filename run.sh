#!/bin/bash

# read cfg file:
if [ -f "cfg" ]; then
    source cfg
fi

if [ -d "src/lac/" ]; then
    cd src/lac/
fi

source .env/bin/activate

python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input
python manage.py creatersakey

gunicorn lac.wsgi:application --bind localhost:11123

