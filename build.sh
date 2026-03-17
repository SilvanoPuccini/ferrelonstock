#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Debug
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ferrelonstock.settings')
import django
django.setup()
from django.conf import settings
print('APPS:', settings.INSTALLED_APPS)
print('DB:', settings.DATABASES['default']['ENGINE'])
"

python manage.py collectstatic --noinput
python manage.py migrate
