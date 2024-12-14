#!/bin/python3
import sys
from django.contrib.auth.models import User

# Password is the first argument
PASSWORD = sys.argv[1]

user = User.objects.get(username='Administrator')
user.set_password('$PASSWORD')
user.save()

print(f"Password for local Administrator user has been set to {PASSWORD}")