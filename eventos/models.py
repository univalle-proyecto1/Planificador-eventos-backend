from django.db import models
from django.conf import settings


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
    horas_estimadas = models.DecimalField(max_digits=4, decimal_places=1)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='NORMAL')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')

    def __str__(self):
        return f"{self.titulo} ({self.evento.nombre})"