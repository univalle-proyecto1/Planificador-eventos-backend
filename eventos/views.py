from django.shortcuts import render

from rest_framework import viewsets
from .models import Evento, TareaLogistica
from .serializers import EventoSerializer, TareaSerializer

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer

class TareaViewSet(viewsets.ModelViewSet):
    queryset = TareaLogistica.objects.all()
    serializer_class = TareaSerializer