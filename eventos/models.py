from django.db import models
from django.conf import settings
from django.utils import timezone


class Evento(models.Model):
    objects = models.Manager()

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eventos',
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=200)
    fecha_evento = models.DateField(null=True, blank=True)
    hora_evento = models.TimeField(null=True, blank=True)
    limite_horas_diarias = models.IntegerField(default=6)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class TareaLogistica(models.Model):
    objects = models.Manager()

    PRIORIDAD_CHOICES = [
        ('NORMAL', 'Normal'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En Progreso'),
        ('HECHO', 'Hecho'),
        ('POSPUESTO', 'Pospuesto'),
    ]

    evento = models.ForeignKey(Evento, related_name='tareas', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    fecha_asignada = models.DateField()
    hora_asignada = models.TimeField(null=True, blank=True)
    horas_estimadas = models.DecimalField(max_digits=4, decimal_places=1)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='NORMAL')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    note = models.TextField(blank=True, default='')
    done_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        estado_incluido = update_fields is None or 'estado' in update_fields
        estado_anterior = None
        if self.pk and estado_incluido:
            estado_anterior = type(self).objects.filter(pk=self.pk).values_list('estado', flat=True).first()

        cambio_estado = estado_incluido and estado_anterior != self.estado
        if cambio_estado:
            self.done_at = timezone.now() if self.estado == 'HECHO' else None
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'done_at'}

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titulo} ({self.evento.nombre})"


class Novedad(models.Model):
    objects = models.Manager()

    EVENTO_CREADO = 'EVENTO_CREADO'
    EVENTO_EDITADO = 'EVENTO_EDITADO'
    SUBTAREA_AGREGADA = 'SUBTAREA_AGREGADA'
    SUBTAREA_COMPLETADA = 'SUBTAREA_COMPLETADA'
    TIPO_CHOICES = [
        (EVENTO_CREADO, 'Evento creado'),
        (EVENTO_EDITADO, 'Evento editado'),
        (SUBTAREA_AGREGADA, 'Subtarea agregada'),
        (SUBTAREA_COMPLETADA, 'Subtarea completada'),
    ]

    evento = models.ForeignKey(Evento, related_name='novedades', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=24, choices=TIPO_CHOICES)
    subtarea_titulo = models.CharField(max_length=200, blank=True, default='')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']