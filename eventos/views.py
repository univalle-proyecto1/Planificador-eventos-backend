from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
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


class TareaViewSet(viewsets.ModelViewSet):
    queryset = TareaLogistica.objects.all()
    serializer_class = TareaSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return TareaLogistica.objects.filter(evento__usuario=self.request.user)
        return TareaLogistica.objects.filter(evento__usuario__isnull=True)



class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request)})


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
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