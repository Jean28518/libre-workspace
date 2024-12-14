#!/bin/bash

# Activate the virtual environment
if [ -f .env/bin/activate ]; then
    source .env/bin/activate
fi

$PASSWORD="$1"

# Set the password for the local Administrator user
python3 manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username='Administrator'); user.set_password('$PASSWORD'); user.save()"

echo "Password for local Administrator user has been set to $PASSWORD"