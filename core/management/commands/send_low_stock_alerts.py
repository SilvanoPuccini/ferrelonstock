from django.core.management.base import BaseCommand

from orders.emails import send_low_stock_notification
from shop.models import Product


class Command(BaseCommand):
    help = (
        'Envía un email de alerta de stock bajo al staff configurado en '
        'NOTIFICATION_EMAIL, con los productos cuyo stock es menor o igual '
        'al umbral indicado (default 5).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=5,
            help='Umbral de stock bajo (default 5).',
        )

    def handle(self, *args, **options):
        threshold = max(options['threshold'], 0)

        products = (
            Product.objects.filter(stock__lte=threshold)
            .select_related('category', 'brand')
            .order_by('stock', 'name')
        )
        count = products.count()
        if count == 0:
            self.stdout.write(
                self.style.WARNING(f'Sin productos bajo stock (umbral: {threshold})')
            )
            return

        send_low_stock_notification(products, threshold)
        self.stdout.write(self.style.SUCCESS(
            f'Email de stock bajo enviado: {count} producto(s) con stock <= {threshold}'
        ))