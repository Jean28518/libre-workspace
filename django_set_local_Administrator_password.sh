#!/bin/bash

. cfg

if [ -d src/lac ]; then
    cd src/lac
fi

# Activate the virtual environment
if [ -f .env/bin/activate ]; then
    source .env/bin/activate
fi

PASSWORD=$1

# Set the password for the local Administrator user
python3 manage.py shell -c "import idm.idm; idm.idm.change_superuser_password('$PASSWORD')"