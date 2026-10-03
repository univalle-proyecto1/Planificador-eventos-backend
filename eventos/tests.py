from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        response = self.client.post('/api/auth/register/', {
            'name': 'Ana Pérez',
            'email': 'ana@example.com',
            'password': 'UnaClaveSegura93!',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(email='ana@example.com').exists())

    def test_register_rejects_duplicate_email(self):
        get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='UnaClaveSegura93!',
        )

        response = self.client.post('/api/auth/register/', {
            'name': 'Ana Pérez',
            'email': 'ANA@example.com',
            'password': 'UnaClaveSegura93!',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data['errors'])

    def test_password_validation_message_is_spanish(self):
        response = self.client.post('/api/auth/register/', {
            'name': 'Ana Pérez',
            'email': 'ana@example.com',
            'password': '12345678',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('contraseña', response.data['errors']['password'].lower())

    def test_login_authenticates_registered_user(self):
        user = get_user_model().objects.create_user(
            username='ana@example.com',
            email='ana@example.com',
            password='UnaClaveSegura93!',
        )

        response = self.client.post('/api/auth/login/', {
            'email': 'ana@example.com',
            'password': 'UnaClaveSegura93!',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.data)

    def test_current_user_and_logout(self):
        user = get_user_model().objects.create_user(
            username='carlos@example.com',
            email='carlos@example.com',
            password='UnaClaveSegura93!',
        )
        self.client.force_login(user)

        res_me = self.client.get('/api/auth/me/')
        self.assertEqual(res_me.status_code, 200)
        self.assertTrue(res_me.data['authenticated'])

        res_logout = self.client.post('/api/auth/logout/')
        self.assertEqual(res_logout.status_code, 200)

        res_me_after = self.client.get('/api/auth/me/')
        self.assertFalse(res_me_after.data['authenticated'])


class EventosApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='Password123!',
        )
        self.user2 = get_user_model().objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            password='Password123!',
        )

    def test_user_only_sees_own_events(self):
        self.client.force_login(self.user1)
        res_create = self.client.post('/api/eventos/', {'nombre': 'Boda User 1', 'limite_horas_diarias': 5}, format='json')
        self.assertEqual(res_create.status_code, 201)

        res_list = self.client.get('/api/eventos/')
        self.assertEqual(len(res_list.data), 1)
        self.assertEqual(res_list.data[0]['nombre'], 'Boda User 1')

        # Switch user
        self.client.force_login(self.user2)
        res_list_user2 = self.client.get('/api/eventos/')
        self.assertEqual(len(res_list_user2.data), 0)

    def test_tarea_daily_hours_limit_validation(self):
        self.client.force_login(self.user1)
        res_evt = self.client.post('/api/eventos/', {'nombre': 'Cumple', 'limite_horas_diarias': 4}, format='json')
        evt_id = res_evt.data['id']

        # Task 1: 3 hours
        res_t1 = self.client.post('/api/tareas/', {
            'evento': evt_id,
            'titulo': 'Decoración',
            'fecha_asignada': '2026-10-15',
            'horas_estimadas': 3.0,
            'prioridad': 'ALTA'
        }, format='json')
        self.assertEqual(res_t1.status_code, 201)

        # Task 2: 2 hours (total 5 > limit 4) -> Should fail
        res_t2 = self.client.post('/api/tareas/', {
            'evento': evt_id,
            'titulo': 'Música',
            'fecha_asignada': '2026-10-15',
            'horas_estimadas': 2.0,
            'prioridad': 'NORMAL'
        }, format='json')
        self.assertEqual(res_t2.status_code, 400)

