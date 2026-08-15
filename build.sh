#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Configurar el Site con el dominio real (links de emails apuntan bien)
python manage.py ensure_site

# Crear superusuario si no existe (requiere ADMIN_PASSWORD)
python manage.py shell -c "
import os
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        raise SystemExit('ADMIN_PASSWORD no definida. Seteá la variable de entorno ADMIN_PASSWORD para crear el superusuario.')
    User.objects.create_superuser('admin', 'admin@ferrelonstock.com', password)
    print('Superusuario creado')
else:
    print('Superusuario ya existe')
"

# Sincronizar datos demo (idempotente: actualiza existentes, no duplica)
python manage.py shell -c "
from shop.models import Product
import subprocess
subprocess.call(['python', 'manage.py', 'load_demo_data'])
subprocess.call(['python', 'manage.py', 'load_brands'])
subprocess.call(['python', 'manage.py', 'load_shipping'])
subprocess.call(['python', 'manage.py', 'load_carriers'])
print(f'Datos demo sincronizados ({Product.objects.count()} productos)')
"

# Asignar imágenes de Cloudinary
python manage.py assign_cloud_images
