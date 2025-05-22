#!/bin/bash

# Because of performance issues of key consitency check at oidc login we disable it
# (https://github.com/juanifioren/django-oidc-provider/issues/374#issuecomment-1109039629)
# Find a path to the file site-packages/Cryptodome/PublicKey/RSA.py
FULL_PATH=$(find -name RSA.py 2>/dev/null | grep site-packages/Cryptodome/PublicKey/RSA.py)
# If file exists replace the the line
# return construct(der[1:6] + [Integer(der[4]).inverse(der[5])]) with
# return construct(der[1:6] + [Integer(der[4]).inverse(der[5])], consistency_check=False)
if [ -f "$FULL_PATH" ]; then
    sed -i 's/return construct(der\[1:6\] + \[Integer(der\[4\]).inverse(der\[5\])\])/return construct(der\[1:6\] + \[Integer(der\[4\]).inverse(der\[5\])\], consistency_check=False)/g' $FULL_PATH
fi

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

