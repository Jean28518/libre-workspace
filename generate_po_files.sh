#!/bin/bash

source /var/lib/libre-workspace/portal/venv/bin/activate

pip install -r /usr/lib/libre-workspace/portal/requirements.txt

# Generate .po files for translations
cd /usr/lib/libre-workspace/portal/
django-admin makemessages -l de
django-admin makemessages -l en