#!/bin/bash

. cfg

if [ -d src/lac ]; then
    cd src/lac
fi

# Activate the virtual environment
if [ -f .env/bin/activate ]; then
    source .env/bin/activate
fi

# If the number of arguments is not equal to 4, then exit
if [ "$#" -ne 4 ]; then
    echo "Illegal number of parameters"
    echo "Usage: $0 <name> <client_id> <client_secret> <redirect_uri>"
    exit 1
fi

CLEANED_DATA="""{
    'name': '$1',
    'client_type': 'confidential',
    'client_id': '$2',
    'client_secret': '$3',
    'response_types': ['1'],
    'jwt_alg': 'RS256',
    'redirect_uris': '$4',
    'require_consent': False,
    'reuse_consent': False,
}"""

echo $CLEANED_DATA

python3 manage.py shell -c "from idm.oidc_provider_settings import add_oidc_provider_client; add_oidc_provider_client($CLEANED_DATA);"

if [ $? -eq 0 ]; then
    echo "OIDC provider client has been added"
else
    echo "Failed to add OIDC provider client"
    exit 1
fi