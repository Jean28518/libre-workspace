#!/bin/bash

# read cfg file:
if [ -f "cfg" ]; then
    source cfg
fi

CHANGED_DIR=false
if [ -d "src/lac/" ]; then
    cd src/lac/
    CHANGED_DIR=true
fi

source .env/bin/activate

if [ "$CHANGED_DIR" = true ]; then
    pip install -r ../../requirements.txt
else
    pip install -r requirements.txt
fi


python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input

echo "Starting server..."
python3 manage.py runserver 0.0.0.0:8000
