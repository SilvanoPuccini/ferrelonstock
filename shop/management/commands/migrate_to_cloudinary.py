import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from shop.models import Product, Category, ProductImage
from accounts.models import UserProfile
from core.models import TeamMember


class Command(BaseCommand):
    help = 'Migra imágenes locales a Cloudinary'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        migrated = 0
        errors = 0

        # Productos
        for product in Product.objects.exclude(image='').exclude(image__isnull=True):
            local_path = os.path.join(media_root, str(product.image))
            if os.path.exists(local_path):
                try:
                    self.stdout.write(f'  Subiendo: {product.name}...')
                    with open(local_path, 'rb') as f:
                        product.image.save(os.path.basename(local_path), File(f), save=True)
                    migrated += 1
                    self.stdout.write(self.style.SUCCESS(f'  OK: {product.name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error: {product.name} - {e}'))
                    errors += 1

        # Categorías
        for cat in Category.objects.exclude(image='').exclude(image__isnull=True):
            local_path = os.path.join(media_root, str(cat.image))
            if os.path.exists(local_path):
                try:
                    self.stdout.write(f'  Subiendo: Categoría {cat.name}...')
                    with open(local_path, 'rb') as f:
                        cat.image.save(os.path.basename(local_path), File(f), save=True)
                    migrated += 1
                except Exception as e:
                    errors += 1

        # Galería de productos
        for img in ProductImage.objects.all():
            local_path = os.path.join(media_root, str(img.image))
            if os.path.exists(local_path):
                try:
                    self.stdout.write(f'  Subiendo: Galería #{img.pk}...')
                    with open(local_path, 'rb') as f:
                        img.image.save(os.path.basename(local_path), File(f), save=True)
                    migrated += 1
                except Exception as e:
                    errors += 1

        # Equipo
        for member in TeamMember.objects.exclude(photo='').exclude(photo__isnull=True):
            local_path = os.path.join(media_root, str(member.photo))
            if os.path.exists(local_path):
                try:
                    self.stdout.write(f'  Subiendo: {member.name}...')
                    with open(local_path, 'rb') as f:
                        member.photo.save(os.path.basename(local_path), File(f), save=True)
                    migrated += 1
                except Exception as e:
                    errors += 1

        # Avatares
        for profile in UserProfile.objects.exclude(avatar='').exclude(avatar__isnull=True):
            local_path = os.path.join(media_root, str(profile.avatar))
            if os.path.exists(local_path):
                try:
                    self.stdout.write(f'  Subiendo: Avatar {profile.user.email}...')
                    with open(local_path, 'rb') as f:
                        profile.avatar.save(os.path.basename(local_path), File(f), save=True)
                    migrated += 1
                except Exception as e:
                    errors += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Migradas: {migrated}'))
        if errors:
            self.stdout.write(self.style.WARNING(f'Errores: {errors}'))
        self.stdout.write(self.style.SUCCESS('Listo! Todas las imágenes están en Cloudinary.'))
