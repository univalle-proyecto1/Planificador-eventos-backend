from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventoViewSet, TareaViewSet

router = DefaultRouter()
router.register(r'eventos', EventoViewSet)
router.register(r'tareas', TareaViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]