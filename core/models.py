from django.db import models


class Contact(models.Model):
    name = models.CharField('Nombre', max_length=100)
    email = models.EmailField('Email')
    subject = models.CharField('Asunto', max_length=200)
    message = models.TextField('Mensaje')
    created_at = models.DateTimeField('Fecha', auto_now_add=True)
    is_read = models.BooleanField('Leído', default=False)

    class Meta:
        verbose_name = 'Mensaje de contacto'
        verbose_name_plural = 'Mensajes de contacto'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.subject}'
