#!/bin/bash

# Activate the virtual environment
if [ -f .env/bin/activate ]; then
    source .env/bin/activate
fi

PASSWORD="$1"

# Set the password for the local Administrator user
python3 django_set_local_Administrator_password.py $PASSWORD