from django.core.management.base import BaseCommand
from shop.models import Category, Product


class Command(BaseCommand):
    help = 'Carga datos de demostración para FerrelonStock'

    def handle(self, *args, **options):
        categories_data = [
            {'name': 'Herramientas Manuales', 'slug': 'herramientas-manuales', 'description': 'Martillos, destornilladores, llaves y más.'},
            {'name': 'Herramientas Eléctricas', 'slug': 'herramientas-electricas', 'description': 'Taladros, amoladoras, sierras eléctricas.'},
            {'name': 'Materiales de Construcción', 'slug': 'materiales-construccion', 'description': 'Cemento, arena, ladrillos, hierro.'},
            {'name': 'Pinturas y Revestimientos', 'slug': 'pinturas-revestimientos', 'description': 'Pinturas, barnices, impermeabilizantes.'},
            {'name': 'Plomería', 'slug': 'plomeria', 'description': 'Cañerías, griferías, conexiones.'},
            {'name': 'Electricidad', 'slug': 'electricidad', 'description': 'Cables, interruptores, tableros.'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat.slug] = cat
            status = 'Creada' if created else 'Ya existía'
            self.stdout.write(f'  {status}: {cat.name}')

        products_data = [
            {'category': 'herramientas-manuales', 'name': 'Martillo carpintero 500g', 'slug': 'martillo-carpintero-500g', 'price': 8990, 'stock': 25, 'description': 'Martillo de carpintero con mango de fibra de vidrio. Cabeza de acero forjado.'},
            {'category': 'herramientas-manuales', 'name': 'Destornillador Phillips PH2', 'slug': 'destornillador-phillips-ph2', 'price': 3490, 'stock': 50, 'description': 'Destornillador Phillips punta magnética. Mango ergonómico antideslizante.'},
            {'category': 'herramientas-manuales', 'name': 'Llave francesa 10"', 'slug': 'llave-francesa-10', 'price': 12990, 'stock': 15, 'description': 'Llave ajustable de 10 pulgadas. Acero al cromo vanadio.'},
            {'category': 'herramientas-manuales', 'name': 'Cinta métrica 5m', 'slug': 'cinta-metrica-5m', 'price': 4990, 'stock': 40, 'description': 'Cinta métrica profesional de 5 metros con freno automático.'},
            {'category': 'herramientas-manuales', 'name': 'Alicate universal 8"', 'slug': 'alicate-universal-8', 'price': 6990, 'stock': 30, 'description': 'Alicate universal con corte lateral. Aislación 1000V.'},
            {'category': 'herramientas-electricas', 'name': 'Taladro percutor 13mm 750W', 'slug': 'taladro-percutor-750w', 'price': 45990, 'stock': 10, 'description': 'Taladro percutor con mandril de 13mm. Motor de 750W. Velocidad variable.'},
            {'category': 'herramientas-electricas', 'name': 'Amoladora angular 4 1/2" 850W', 'slug': 'amoladora-angular-850w', 'price': 35990, 'stock': 12, 'description': 'Amoladora angular con disco de 115mm. Motor de 850W.'},
            {'category': 'herramientas-electricas', 'name': 'Sierra caladora 600W', 'slug': 'sierra-caladora-600w', 'price': 39990, 'stock': 8, 'description': 'Sierra caladora con velocidad variable. Corte en madera hasta 65mm.'},
            {'category': 'herramientas-electricas', 'name': 'Atornillador inalámbrico 12V', 'slug': 'atornillador-inalambrico-12v', 'price': 29990, 'stock': 20, 'description': 'Atornillador a batería de litio 12V. Incluye 2 baterías y cargador.'},
            {'category': 'materiales-construccion', 'name': 'Cemento Portland 50kg', 'slug': 'cemento-portland-50kg', 'price': 7990, 'stock': 100, 'description': 'Cemento Portland de alta resistencia. Bolsa de 50 kilos.'},
            {'category': 'materiales-construccion', 'name': 'Hierro de construcción 8mm x 12m', 'slug': 'hierro-construccion-8mm', 'price': 5490, 'stock': 200, 'description': 'Barra de hierro nervurado de 8mm de diámetro por 12 metros.'},
            {'category': 'materiales-construccion', 'name': 'Ladrillo hueco 12x18x33', 'slug': 'ladrillo-hueco-12x18x33', 'price': 190, 'stock': 5000, 'description': 'Ladrillo cerámico hueco. Medidas: 12x18x33 cm. Precio por unidad.'},
            {'category': 'materiales-construccion', 'name': 'Arena gruesa x m3', 'slug': 'arena-gruesa-m3', 'price': 25990, 'stock': 50, 'description': 'Arena gruesa lavada para construcción. Precio por metro cúbico.'},
            {'category': 'pinturas-revestimientos', 'name': 'Pintura látex interior 20L', 'slug': 'pintura-latex-interior-20l', 'price': 32990, 'stock': 15, 'description': 'Pintura látex para interiores color blanco. Rendimiento: 10-12 m²/L.'},
            {'category': 'pinturas-revestimientos', 'name': 'Membrana líquida 20L', 'slug': 'membrana-liquida-20l', 'price': 45990, 'stock': 8, 'description': 'Membrana líquida impermeabilizante para techos y terrazas.'},
            {'category': 'pinturas-revestimientos', 'name': 'Rodillo antigota 22cm', 'slug': 'rodillo-antigota-22cm', 'price': 4990, 'stock': 35, 'description': 'Rodillo de lana sintética antigota. Ideal para pintura látex.'},
            {'category': 'plomeria', 'name': 'Caño PVC 110mm x 4m', 'slug': 'cano-pvc-110mm-4m', 'price': 8990, 'stock': 30, 'description': 'Caño de PVC para desagüe cloacal. Diámetro 110mm, largo 4 metros.'},
            {'category': 'plomeria', 'name': 'Grifería monocomando cocina', 'slug': 'griferia-monocomando-cocina', 'price': 24990, 'stock': 10, 'description': 'Grifería monocomando para cocina. Acabado cromado. Pico alto giratorio.'},
            {'category': 'electricidad', 'name': 'Cable unipolar 2.5mm² x 100m', 'slug': 'cable-unipolar-25mm-100m', 'price': 18990, 'stock': 20, 'description': 'Cable unipolar de cobre 2.5mm². Rollo de 100 metros. Color celeste.'},
            {'category': 'electricidad', 'name': 'Térmico bipolar 20A', 'slug': 'termico-bipolar-20a', 'price': 9990, 'stock': 25, 'description': 'Interruptor termomagnético bipolar de 20 Amperes.'},
        ]

        for prod_data in products_data:
            category = categories[prod_data.pop('category')]
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={**prod_data, 'category': category}
            )
            status = 'Creado' if created else 'Ya existía'
            self.stdout.write(f'  {status}: {product.name}')

        self.stdout.write(self.style.SUCCESS('\n¡Datos de demostración cargados con éxito!'))
