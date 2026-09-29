from rest_framework import serializers
from .models import Evento, TareaLogistica

class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaLogistica
        fields = '__all__'

class EventoSerializer(serializers.ModelSerializer):
    tareas = TareaSerializer(many=True, read_only=True)
    class Meta:
        model = Evento
        fields = '__all__'