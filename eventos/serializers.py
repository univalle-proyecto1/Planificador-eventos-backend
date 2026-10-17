from rest_framework import serializers
from .models import Evento, Novedad, TareaLogistica
from django.db.models import Sum
from django.utils import timezone


class TareaStatusField(serializers.Field):
    ESTADO_POR_STATUS = {
        'pending': 'PENDIENTE',
        'in_progress': 'EN_PROGRESO',
        'done': 'HECHO',
        'postponed': 'POSPUESTO',
        'PENDIENTE': 'PENDIENTE',
        'EN_PROGRESO': 'EN_PROGRESO',
        'HECHO': 'HECHO',
        'POSPUESTO': 'POSPUESTO',
    }
    STATUS_POR_ESTADO = {estado: status for status, estado in ESTADO_POR_STATUS.items() if status.islower()}

    def to_representation(self, value):
        return self.STATUS_POR_ESTADO.get(value, value)

    def to_internal_value(self, data):
        try:
            return self.ESTADO_POR_STATUS[data]
        except (KeyError, TypeError) as exc:
            raise serializers.ValidationError('Estado inválido.') from exc


class TareaSerializer(serializers.ModelSerializer):
    status = TareaStatusField(source='estado', required=False)

    class Meta:
        model = TareaLogistica
        fields = '__all__'

    def validate(self, attrs):
        evento = attrs.get('evento') or (self.instance.evento if self.instance else None)
        fecha_asignada = attrs.get('fecha_asignada') or (self.instance.fecha_asignada if self.instance else None)
        horas_estimadas = attrs.get('horas_estimadas') or (self.instance.horas_estimadas if self.instance else 0)

        if 'fecha_asignada' in attrs and fecha_asignada < timezone.localdate():
            raise serializers.ValidationError({
                'fecha_asignada': 'No se puede programar una subtarea en una fecha anterior a hoy.'
            })

        if evento and fecha_asignada and horas_estimadas:
            # Obtener horas acumuladas exceptuando la tarea actual si se está editando
            qs = TareaLogistica.objects.filter(evento=evento, fecha_asignada=fecha_asignada)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            horas_actuales = qs.aggregate(total=Sum('horas_estimadas'))['total'] or 0
            horas_totales = float(horas_actuales) + float(horas_estimadas)
            limite = float(evento.limite_horas_diarias)

            if horas_totales > limite:
                horas_disponibles = max(0, limite - float(horas_actuales))
                raise serializers.ValidationError(
                    f"No se puede superar el límite diario de {limite} horas para {fecha_asignada}. "
                    f"Actualmente tienes {horas_disponibles:g} horas disponibles."
                )

        return attrs

class EventoSerializer(serializers.ModelSerializer):
    tareas = TareaSerializer(many=True, read_only=True)
    class Meta:
        model = Evento
        fields = '__all__'
        read_only_fields = ['usuario']

    def validate_fecha_evento(self, value):
        if value and value < timezone.localdate():
            raise serializers.ValidationError('No se puede programar un evento en una fecha anterior a hoy.')
        return value


class NovedadSerializer(serializers.ModelSerializer):
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)

    class Meta:
        model = Novedad
        fields = ['id', 'evento', 'evento_nombre', 'tipo', 'subtarea_titulo', 'fecha']