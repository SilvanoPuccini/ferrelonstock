#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Debug: verificar que Django carga
python -c "import django; print(f'Django {django.VERSION} OK')"
python manage.py help 2>&1 | head -5

python manage.py collectstatic --noinput
python manage.py migrate
