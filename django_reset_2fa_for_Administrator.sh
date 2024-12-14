#!/bin/bash

. cfg

if [ -d src/lac ]; then
    cd src/lac
fi

# Activate the virtual environment
if [ -f .env/bin/activate ]; then
    source .env/bin/activate
fi

python3 manage.py shell -c "from idm.idm import reset_2fa_for; reset_2fa_for('Administrator')"

echo "2FA for Administrator has been reset"