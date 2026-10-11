from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from datetime import timedelta, date
from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Evento, TareaLogistica
from .serializers import EventoSerializer, TareaSerializer


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Evento.objects.filter(usuario=self.request.user)
        return Evento.objects.filter(usuario__isnull=True)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(usuario=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='reprogramar')
    def reprogramar(self, request, pk=None):
        evento = self.get_object()
        nueva_fecha_evento = request.data.get('fecha_evento')
        dias_desplazamiento = request.data.get('dias_desplazamiento')
        nueva_fecha_base = request.data.get('nueva_fecha_base')

        if nueva_fecha_evento is not None:
            if nueva_fecha_evento == '' or nueva_fecha_evento is False:
                evento.fecha_evento = None
            else:
                evento.fecha_evento = nueva_fecha_evento
            evento.save()

        tareas_pendientes = list(evento.tareas.exclude(estado='HECHO').order_by('fecha_asignada'))
        if not tareas_pendientes and dias_desplazamiento is None and nueva_fecha_base is None:
            return Response(EventoSerializer(evento).data)

        delta = None
        if dias_desplazamiento is not None:
            try:
                delta = timedelta(days=int(dias_desplazamiento))
            except (ValueError, TypeError):
                return Response({'detail': 'Los días de desplazamiento deben ser un número entero.'}, status=400)
        elif nueva_fecha_base:
            try:
                base_dt = date.fromisoformat(str(nueva_fecha_base))
                if tareas_pendientes:
                    primera_fecha = tareas_pendientes[0].fecha_asignada
                    delta = timedelta(days=(base_dt - primera_fecha).days)
                else:
                    delta = timedelta(days=0)
            except (ValueError, TypeError):
                return Response({'detail': 'Formato de fecha inválido para nueva_fecha_base.'}, status=400)

        if delta is not None and delta.days != 0 and tareas_pendientes:
            limite = float(evento.limite_horas_diarias)
            nuevas_fechas = {}
            horas_por_fecha = {}

            for t in tareas_pendientes:
                nf = t.fecha_asignada + delta
                nuevas_fechas[t.id] = nf
                horas_por_fecha[nf] = horas_por_fecha.get(nf, 0) + float(t.horas_estimadas)

            for nf, horas_movidas in horas_por_fecha.items():
                horas_hechas = evento.tareas.filter(estado='HECHO', fecha_asignada=nf).aggregate(total=Sum('horas_estimadas'))['total'] or 0
                total_horas = float(horas_hechas) + float(horas_movidas)
                if total_horas > limite:
                    return Response({
                        'detail': f"La reprogramación superaría el límite de {limite} horas para la fecha {nf} (total proyectado: {total_horas}h)."
                    }, status=400)

            with transaction.atomic():
                for t in tareas_pendientes:
                    t.fecha_asignada = nuevas_fechas[t.id]
                    if t.estado == 'POSPUESTO':
                        t.estado = 'PENDIENTE'
                    t.save()

        evento.refresh_from_db()
        return Response(EventoSerializer(evento).data)


class TareaViewSet(viewsets.ModelViewSet):
    queryset = TareaLogistica.objects.all()
    serializer_class = TareaSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return TareaLogistica.objects.filter(evento__usuario=self.request.user)
        return TareaLogistica.objects.filter(evento__usuario__isnull=True)

    @action(detail=True, methods=['post', 'patch'], url_path='reprogramar')
    def reprogramar(self, request, pk=None):
        tarea = self.get_object()
        nueva_fecha = request.data.get('fecha_asignada')
        if not nueva_fecha:
            return Response({'detail': 'Debes especificar una fecha_asignada válida.'}, status=400)

        datos = {'fecha_asignada': nueva_fecha}
        if 'horas_estimadas' in request.data:
            datos['horas_estimadas'] = request.data['horas_estimadas']
        if 'estado' in request.data:
            datos['estado'] = request.data['estado']
        elif tarea.estado == 'POSPUESTO':
            datos['estado'] = 'PENDIENTE'

        serializer = TareaSerializer(tarea, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request)})


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        errors = {}

        if not name:
            errors['name'] = 'Ingresa tu nombre.'
        elif len(name) > 150:
            errors['name'] = 'El nombre no puede superar 150 caracteres.'

        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Ingresa un correo electrónico válido.'

        if len(email) > 150:
            errors['email'] = 'El correo no puede superar 150 caracteres.'
        elif get_user_model().objects.filter(email__iexact=email).exists():
            errors['email'] = 'Ya existe una cuenta con este correo.'

        if not password:
            errors['password'] = 'Ingresa una contraseña.'
        else:
            try:
                validate_password(password)
            except ValidationError as error:
                errors['password'] = ' '.join(error.messages)

        if errors:
            return Response({'message': 'Revisa los datos del formulario.', 'errors': errors}, status=400)

        user_model = get_user_model()
        user_model.objects.create_user(
            username=email,
            email=email,
            first_name=name,
            password=password,
        )
        return Response({'message': 'Cuenta creada.'}, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        user = get_user_model().objects.filter(email__iexact=email).first()
        authenticated_user = authenticate(
            request,
            username=user.get_username() if user else email,
            password=password,
        )

        if authenticated_user is None:
            return Response({'message': 'Correo o contraseña incorrectos.'}, status=401)

        login(request, authenticated_user)
        return Response({
            'message': 'Sesión iniciada.',
            'user': {
                'id': authenticated_user.id,
                'name': authenticated_user.first_name or authenticated_user.username,
                'email': authenticated_user.email,
            }
        })


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({'message': 'Sesión cerrada.'})


class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': {
                    'id': request.user.id,
                    'name': request.user.first_name or request.user.username,
                    'email': request.user.email,
                }
            })
        return Response({'authenticated': False, 'user': None})