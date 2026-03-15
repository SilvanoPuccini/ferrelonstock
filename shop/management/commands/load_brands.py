from django.core.management.base import BaseCommand
from shop.models import Brand, Product


class Command(BaseCommand):
    help = 'Carga marcas de demostración y las asigna a productos'

    def handle(self, *args, **options):
        brands_data = [
            {'name': 'Bosch', 'slug': 'bosch'},
            {'name': 'Stanley', 'slug': 'stanley'},
            {'name': 'DeWalt', 'slug': 'dewalt'},
            {'name': 'Makita', 'slug': 'makita'},
            {'name': 'Black+Decker', 'slug': 'black-decker'},
            {'name': 'Truper', 'slug': 'truper'},
            {'name': 'Loctite', 'slug': 'loctite'},
            {'name': 'Alba', 'slug': 'alba'},
            {'name': 'Tigre', 'slug': 'tigre'},
            {'name': 'FV', 'slug': 'fv'},
        ]

        brands = {}
        for b in brands_data:
            brand, created = Brand.objects.get_or_create(slug=b['slug'], defaults=b)
            brands[brand.slug] = brand
            status = 'Creada' if created else 'Ya existía'
            self.stdout.write(f'  {status}: {brand.name}')

        assignments = {
            'martillo-carpintero-500g': 'stanley',
            'destornillador-phillips-ph2': 'stanley',
            'llave-francesa-10': 'stanley',
            'cinta-metrica-5m': 'truper',
            'alicate-universal-8': 'truper',
            'taladro-percutor-750w': 'bosch',
            'amoladora-angular-850w': 'dewalt',
            'sierra-caladora-600w': 'makita',
            'atornillador-inalambrico-12v': 'black-decker',
            'cemento-portland-50kg': 'loctite',
            'pintura-latex-interior-20l': 'alba',
            'membrana-liquida-20l': 'alba',
            'rodillo-antigota-22cm': 'truper',
            'cano-pvc-110mm-4m': 'tigre',
            'griferia-monocomando-cocina': 'fv',
            'cable-unipolar-25mm-100m': 'tigre',
            'termico-bipolar-20a': 'bosch',
        }

        for slug, brand_slug in assignments.items():
            try:
                product = Product.objects.get(slug=slug)
                product.brand = brands[brand_slug]
                product.save()
                self.stdout.write(f'  Asignada {brands[brand_slug].name} a {product.name}')
            except Product.DoesNotExist:
                pass

        self.stdout.write(self.style.SUCCESS('\n¡Marcas cargadas y asignadas!'))
