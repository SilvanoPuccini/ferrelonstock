#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Crear superusuario si no existe
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@ferrelonstock.com', 'FerrelonAdmin2026!')
    print('Superusuario creado')
else:
    print('Superusuario ya existe')
"

# Cargar datos demo si no hay productos
python manage.py shell -c "
from shop.models import Product
if Product.objects.count() == 0:
    import subprocess
    subprocess.call(['python', 'manage.py', 'load_demo_data'])
    subprocess.call(['python', 'manage.py', 'load_brands'])
    subprocess.call(['python', 'manage.py', 'load_shipping'])
    subprocess.call(['python', 'manage.py', 'load_carriers'])
    print('Datos demo cargados')
else:
    print(f'Ya hay {Product.objects.count()} productos')
"

# Asignar imágenes de Cloudinary
python manage.py assign_cloud_images
