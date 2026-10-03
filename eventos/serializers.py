from rest_framework import serializers
from .models import Evento, TareaLogistica
from django.db.models import Sum

class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaLogistica
        fields = '__all__'

    def validate(self, attrs):
        evento = attrs.get('evento') or (self.instance.evento if self.instance else None)
        fecha_asignada = attrs.get('fecha_asignada') or (self.instance.fecha_asignada if self.instance else None)
        horas_estimadas = attrs.get('horas_estimadas') or (self.instance.horas_estimadas if self.instance else 0)

        if evento and fecha_asignada and horas_estimadas:
            # Obtener horas acumuladas exceptuando la tarea actual si se está editando
            qs = TareaLogistica.objects.filter(evento=evento, fecha_asignada=fecha_asignada)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            horas_actuales = qs.aggregate(total=Sum('horas_estimadas'))['total'] or 0
            horas_totales = float(horas_actuales) + float(horas_estimadas)
            limite = float(evento.limite_horas_diarias)

            if horas_totales > limite:
                raise serializers.ValidationError(
                    f"Supera el límite de {limite} horas diarias permitidas para la fecha {fecha_asignada}. "
                    f"Actualmente tienes {horas_actuales} hrs ocupadas."
                )

        return attrs

class EventoSerializer(serializers.ModelSerializer):
    tareas = TareaSerializer(many=True, read_only=True)
    class Meta:
        model = Evento
        fields = '__all__'
        read_only_fields = ['usuario']