import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from shop.models import Product


# Mapeo: slug del producto → búsqueda específica en Unsplash source API
# Usando Unsplash Source con términos ultra-específicos
PRODUCT_IMAGES = {
    # Herramientas Manuales
    'martillo-carpintero-500g': 'https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=600&h=600&fit=crop',
    'destornillador-phillips-ph2': 'https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=600&h=600&fit=crop',
    'llave-francesa-10': 'https://images.unsplash.com/photo-1580901368919-7738efb0f87e?w=600&h=600&fit=crop',
    'cinta-metrica-5m': 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600&h=600&fit=crop',
    'alicate-universal-8': 'https://images.unsplash.com/photo-1513346940221-6f673d962e97?w=600&h=600&fit=crop',

    # Herramientas Eléctricas
    'taladro-percutor-750w': 'https://images.unsplash.com/photo-1504148455328-c376907d081c?w=600&h=600&fit=crop',
    'amoladora-angular-850w': 'https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=600&h=600&fit=crop&crop=left',
    'sierra-caladora-600w': 'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=600&h=600&fit=crop',
    'atornillador-inalambrico-12v': 'https://images.unsplash.com/photo-1530124566582-a45a7e5ff900?w=600&h=600&fit=crop',

    # Electricidad
    'cable-unipolar-25mm-100m': 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=600&h=600&fit=crop',
    'termico-bipolar-20a': 'https://images.unsplash.com/photo-1621905252507-b35492cc74b4?w=600&h=600&fit=crop',

    # Pinturas y Revestimientos
    'pintura-latex-interior-20l': 'https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=600&h=600&fit=crop',
    'rodillo-antigota-22cm': 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=600&h=600&fit=crop',
    'membrana-liquida-20l': 'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=600&h=600&fit=crop',

    # Plomería
    'griferia-monocomando-cocina': 'https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=600&h=600&fit=crop',
    'cano-pvc-110mm-4m': 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=600&h=600&fit=crop',

    # Materiales de Construcción
    'cemento-portland-50kg': 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&h=600&fit=crop',
    'hierro-construccion-8mm': 'https://images.unsplash.com/photo-1517089596392-fb9a9033e05b?w=600&h=600&fit=crop',
    'ladrillo-hueco-12x18x33': 'https://images.unsplash.com/photo-1590075865003-e48277faa558?w=600&h=600&fit=crop',
    'arena-gruesa-m3': 'https://images.unsplash.com/photo-1517089596392-fb9a9033e05b?w=600&h=600&fit=crop&crop=bottom',
}

# Fallback: buscar por categoría si no hay match exacto
CATEGORY_FALLBACKS = {
    'Herramientas Manuales': 'https://images.unsplash.com/photo-1581783898377-1c85bf937427?w=600&h=600&fit=crop',
    'Herramientas Eléctricas': 'https://images.unsplash.com/photo-1504148455328-c376907d081c?w=600&h=600&fit=crop',
    'Electricidad': 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=600&h=600&fit=crop',
    'Pinturas y Revestimientos': 'https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=600&h=600&fit=crop',
    'Plomería': 'https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=600&h=600&fit=crop',
    'Materiales de Construcción': 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&h=600&fit=crop',
    'Jardín y Exterior': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&h=600&fit=crop',
}


class Command(BaseCommand):
    help = 'Descarga imágenes de Unsplash y las asigna a los productos'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Reemplazar imágenes existentes')

    def handle(self, *args, **options):
        force = options['force']
        products = Product.objects.select_related('category').all()
        downloaded = 0
        skipped = 0
        errors = 0

        for product in products:
            if product.image and not force:
                self.stdout.write(f'  ⏭️  {product.name} (ya tiene imagen)')
                skipped += 1
                continue

            # Buscar URL por slug exacto
            image_url = PRODUCT_IMAGES.get(product.slug)

            # Fallback por categoría
            if not image_url:
                image_url = CATEGORY_FALLBACKS.get(product.category.name, '')

            if not image_url:
                self.stdout.write(self.style.WARNING(f'  ⚠️  {product.name} - Sin imagen'))
                errors += 1
                continue

            try:
                self.stdout.write(f'  ⬇️  {product.name}...')
                response = requests.get(image_url, timeout=20, allow_redirects=True)
                response.raise_for_status()

                filename = f'{product.slug}.jpg'
                product.image.save(filename, ContentFile(response.content), save=True)
                downloaded += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅  {product.name}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌  {product.name} - {e}'))
                errors += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Descargadas: {downloaded}'))
        self.stdout.write(f'⏭️  Salteadas: {skipped}')
        if errors:
            self.stdout.write(self.style.WARNING(f'⚠️  Errores: {errors}'))
