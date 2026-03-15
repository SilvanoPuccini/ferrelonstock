from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    address = models.CharField('Dirección', max_length=250, blank=True)
    city = models.CharField('Ciudad', max_length=100, blank=True)
    region = models.CharField('Región/Provincia', max_length=100, blank=True)
    postal_code = models.CharField('Código postal', max_length=20, blank=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f'Perfil de {self.user.email}'

    def get_initials(self):
        if self.user.first_name and self.user.last_name:
            return f'{self.user.first_name[0]}{self.user.last_name[0]}'.upper()
        return self.user.email[0:2].upper()


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()
