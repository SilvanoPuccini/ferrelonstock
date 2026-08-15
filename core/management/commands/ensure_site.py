from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = (
        'Configura el Site de Django (django.contrib.sites) con el dominio '
        'real, para que los links absolutos de los emails apunten al sitio '
        'correcto (ej. confirmación de email, reset de contraseña).'
    )

    def handle(self, *args, **options):
        domain = getattr(settings, 'SITE_DOMAIN', '') or 'ferrelonstock.onrender.com'
        site, created = Site.objects.get_or_create(pk=settings.SITE_ID)
        site.domain = domain
        site.name = domain
        site.save()
        verb = 'Creado' if created else 'Actualizado'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} Site #{site.pk}: {site.domain}'
        ))
