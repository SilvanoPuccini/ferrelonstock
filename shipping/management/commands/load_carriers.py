from django.core.management.base import BaseCommand
from shipping.models import Carrier


class Command(BaseCommand):
    help = 'Carga transportistas'

    def handle(self, *args, **options):
        carriers = [
            {
                'name': 'Andreani',
                'code': 'andreani',
                'tracking_url': 'https://www.andreani.com/#!/informacionEnvio/{tracking_number}',
                'phone': '0800-122-1111',
            },
            {
                'name': 'OCA',
                'code': 'oca',
                'tracking_url': 'https://www5.oca.com.ar/ocaepakNet/Views/ConsultaTracking/TrackingConsult.aspx?numberTracking={tracking_number}',
                'phone': '0800-999-7700',
            },
            {
                'name': 'Correo Argentino',
                'code': 'correo-argentino',
                'tracking_url': 'https://www.correoargentino.com.ar/formularios/ondnc?id={tracking_number}',
                'phone': '0810-999-0102',
            },
            {
                'name': 'Mercado Envíos',
                'code': 'mercado-envios',
                'tracking_url': '',
                'phone': '',
            },
        ]

        for c in carriers:
            obj, created = Carrier.objects.get_or_create(code=c['code'], defaults=c)
            self.stdout.write(f'  {"Creado" if created else "Ya existía"}: {obj.name}')

        self.stdout.write(self.style.SUCCESS('\n¡Transportistas cargados!'))
