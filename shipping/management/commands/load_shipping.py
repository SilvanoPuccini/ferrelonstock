from django.core.management.base import BaseCommand
from shipping.models import ShippingZone, ShippingMethod, ShippingConfig


class Command(BaseCommand):
    help = 'Carga datos de envío'

    def handle(self, *args, **options):
        # Configuración global
        ShippingConfig.get_config()
        self.stdout.write('  Config creada (envío gratis desde $50.000)')

        # Métodos
        methods = [
            {'name': 'Retiro en local', 'code': 'pickup', 'method_type': 'pickup', 'description': 'Retirá tu pedido en nuestro local sin costo'},
            {'name': 'Envío estándar', 'code': 'standard', 'method_type': 'standard', 'description': 'Envío a domicilio con seguimiento'},
            {'name': 'Envío express', 'code': 'express', 'method_type': 'express', 'description': 'Envío prioritario con entrega rápida'},
        ]
        for m in methods:
            obj, created = ShippingMethod.objects.get_or_create(code=m['code'], defaults=m)
            self.stdout.write(f'  {"Creado" if created else "Ya existía"}: {obj.name}')

        # Zonas
        zones = [
            {'name': 'CABA', 'code': 'caba', 'base_price': 2500, 'estimated_days_min': 1, 'estimated_days_max': 2},
            {'name': 'Gran Buenos Aires', 'code': 'gba', 'base_price': 3500, 'estimated_days_min': 2, 'estimated_days_max': 4},
            {'name': 'Buenos Aires Interior', 'code': 'bsas-int', 'base_price': 4500, 'estimated_days_min': 3, 'estimated_days_max': 5},
            {'name': 'Centro (Córdoba, Santa Fe, Entre Ríos)', 'code': 'centro', 'base_price': 5500, 'estimated_days_min': 3, 'estimated_days_max': 6},
            {'name': 'Norte (Tucumán, Salta, Jujuy, Misiones)', 'code': 'norte', 'base_price': 7000, 'estimated_days_min': 5, 'estimated_days_max': 8},
            {'name': 'Cuyo (Mendoza, San Juan, San Luis)', 'code': 'cuyo', 'base_price': 6500, 'estimated_days_min': 4, 'estimated_days_max': 7},
            {'name': 'Patagonia (Neuquén, Río Negro, Chubut, Santa Cruz, TdF)', 'code': 'patagonia', 'base_price': 8500, 'estimated_days_min': 5, 'estimated_days_max': 10},
        ]
        for z in zones:
            obj, created = ShippingZone.objects.get_or_create(code=z['code'], defaults=z)
            self.stdout.write(f'  {"Creada" if created else "Ya existía"}: {obj.name} - ${obj.base_price:,.0f}')

        self.stdout.write(self.style.SUCCESS('\n¡Datos de envío cargados!'))
