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

    def test_past_event_and_task_dates_are_rejected_on_create_and_update(self):
        self.client.force_login(self.user1)
        past_date = '2000-01-01'

        past_event = self.client.post('/api/eventos/', {
            'nombre': 'Evento pasado',
            'fecha_evento': past_date,
        }, format='json')
        self.assertEqual(past_event.status_code, 400)
        self.assertIn('fecha_evento', past_event.data)

        event = self.client.post('/api/eventos/', {'nombre': 'Evento válido'}, format='json')
        event_id = event.data['id']
        event_update = self.client.patch(f'/api/eventos/{event_id}/', {
            'fecha_evento': past_date,
        }, format='json')
        self.assertEqual(event_update.status_code, 400)
        self.assertIn('fecha_evento', event_update.data)

        past_task = self.client.post('/api/tareas/', {
            'evento': event_id,
            'titulo': 'Tarea pasada',
            'fecha_asignada': past_date,
            'horas_estimadas': 1,
        }, format='json')
        self.assertEqual(past_task.status_code, 400)
        self.assertIn('fecha_asignada', past_task.data)

        task = self.client.post('/api/tareas/', {
            'evento': event_id,
            'titulo': 'Tarea válida',
            'fecha_asignada': '2099-01-01',
            'horas_estimadas': 1,
        }, format='json')
        task_update = self.client.patch(f"/api/tareas/{task.data['id']}/", {
            'fecha_asignada': past_date,
        }, format='json')
        self.assertEqual(task_update.status_code, 400)
        self.assertIn('fecha_asignada', task_update.data)

    def test_novedades_register_activity_and_are_private_to_event_owner(self):
        self.client.force_login(self.user1)
        created = self.client.post('/api/eventos/', {'nombre': 'Evento inicial'}, format='json')
        event_id = created.data['id']
        self.client.patch(f'/api/eventos/{event_id}/', {'nombre': 'Evento actualizado'}, format='json')
        task = self.client.post('/api/tareas/', {
            'evento': event_id,
            'titulo': 'Reservar local',
            'fecha_asignada': '2026-12-19',
            'horas_estimadas': 1,
        }, format='json')
        self.client.patch(f"/api/tareas/{task.data['id']}/", {'status': 'done'}, format='json')

        response = self.client.get('/api/novedades/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [novedad['tipo'] for novedad in response.data],
            ['SUBTAREA_COMPLETADA', 'SUBTAREA_AGREGADA', 'EVENTO_EDITADO', 'EVENTO_CREADO'],
        )
        self.assertEqual(response.data[0]['subtarea_titulo'], 'Reservar local')
        self.assertEqual(response.data[0]['evento_nombre'], 'Evento actualizado')

        self.client.force_login(self.user2)
        other_user_response = self.client.get('/api/novedades/')
        self.assertEqual(other_user_response.status_code, 200)
        self.assertEqual(other_user_response.data, [])

    def test_tarea_daily_hours_limit_validation(self):
        self.client.force_login(self.user1)
        res_evt = self.client.post('/api/eventos/', {'nombre': 'Cumple', 'limite_horas_diarias': 4}, format='json')
        evt_id = res_evt.data['id']

        # Task 1: 3 hours
        res_t1 = self.client.post('/api/tareas/', {
            'evento': evt_id,
            'titulo': 'Decoración',
            'fecha_asignada': '2026-10-17',
            'horas_estimadas': 3.0,
            'prioridad': 'ALTA'
        }, format='json')
        self.assertEqual(res_t1.status_code, 201)

        # Task 2: 2 hours (total 5 > limit 4) -> Should fail
        res_t2 = self.client.post('/api/tareas/', {
            'evento': evt_id,
            'titulo': 'Música',
            'fecha_asignada': '2026-10-17',
            'horas_estimadas': 2.0,
            'prioridad': 'NORMAL'
        }, format='json')
        self.assertEqual(res_t2.status_code, 400)

    def test_task_hours_can_be_edited_and_limit_reports_available_hours(self):
        self.client.force_login(self.user1)
        event_response = self.client.post('/api/eventos/', {
            'nombre': 'Evento con límite',
            'limite_horas_diarias': 4,
        }, format='json')
        event_id = event_response.data['id']
        task_data = {
            'evento': event_id,
            'fecha_asignada': '2026-12-19',
            'horas_estimadas': 1.5,
        }
        self.client.post('/api/tareas/', {
            **task_data,
            'titulo': 'Preparación',
        }, format='json')
        second_task = self.client.post('/api/tareas/', {
            **task_data,
            'titulo': 'Montaje',
        }, format='json')
        task_url = f"/api/tareas/{second_task.data['id']}/"

        updated = self.client.patch(task_url, {'horas_estimadas': 2.5}, format='json')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(float(updated.data['horas_estimadas']), 2.5)

        rejected = self.client.patch(task_url, {'horas_estimadas': 3}, format='json')
        self.assertEqual(rejected.status_code, 400)
        self.assertIn('2.5 horas disponibles', str(rejected.data))

    def test_event_and_task_schedule_can_be_updated(self):
        self.client.force_login(self.user1)
        event_response = self.client.post('/api/eventos/', {
            'nombre': 'Evento original',
            'limite_horas_diarias': 6,
        }, format='json')
        event_id = event_response.data['id']

        updated_event = self.client.patch(f'/api/eventos/{event_id}/', {
            'nombre': 'Evento actualizado',
            'fecha_evento': '2026-12-20',
            'hora_evento': '18:30:00',
            'limite_horas_diarias': 8,
        }, format='json')

        self.assertEqual(updated_event.status_code, 200)
        self.assertEqual(updated_event.data['nombre'], 'Evento actualizado')
        self.assertEqual(updated_event.data['fecha_evento'], '2026-12-20')
        self.assertEqual(updated_event.data['hora_evento'], '18:30:00')
        self.assertEqual(updated_event.data['limite_horas_diarias'], 8)

        task_response = self.client.post('/api/tareas/', {
            'evento': event_id,
            'titulo': 'Subtarea original',
            'fecha_asignada': '2026-12-19',
            'hora_asignada': '10:00:00',
            'horas_estimadas': 1,
        }, format='json')
        task_id = task_response.data['id']

        updated_task = self.client.patch(f'/api/tareas/{task_id}/', {
            'titulo': 'Subtarea actualizada',
            'fecha_asignada': '2026-12-21',
            'hora_asignada': '11:30:00',
        }, format='json')

        self.assertEqual(updated_task.status_code, 200)
        self.assertEqual(updated_task.data['titulo'], 'Subtarea actualizada')
        self.assertEqual(updated_task.data['fecha_asignada'], '2026-12-21')
        self.assertEqual(updated_task.data['hora_asignada'], '11:30:00')

    def test_task_patch_preserves_note_and_sets_done_at(self):
        self.client.force_login(self.user1)
        event_response = self.client.post('/api/eventos/', {'nombre': 'Evento'}, format='json')
        task_response = self.client.post('/api/tareas/', {
            'evento': event_response.data['id'],
            'titulo': 'Confirmar proveedor',
            'fecha_asignada': '2026-12-19',
            'horas_estimadas': 1,
        }, format='json')
        task_url = f"/api/tareas/{task_response.data['id']}/"

        postponed = self.client.patch(task_url, {
            'status': 'postponed',
            'note': 'El proveedor pidió cambiar la fecha.',
        }, format='json')
        self.assertEqual(postponed.status_code, 200)
        self.assertEqual(postponed.data['estado'], 'POSPUESTO')
        self.assertEqual(postponed.data['status'], 'postponed')
        self.assertEqual(postponed.data['note'], 'El proveedor pidió cambiar la fecha.')
        self.assertIsNone(postponed.data['done_at'])

        resumed = self.client.patch(task_url, {'status': 'in_progress'}, format='json')
        self.assertEqual(resumed.status_code, 200)
        self.assertEqual(resumed.data['estado'], 'EN_PROGRESO')
        self.assertEqual(resumed.data['note'], 'El proveedor pidió cambiar la fecha.')

        self.client.patch(task_url, {'status': 'postponed'}, format='json')
        completed = self.client.patch(task_url, {'status': 'done'}, format='json')
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data['estado'], 'HECHO')
        self.assertEqual(completed.data['status'], 'done')
        self.assertEqual(completed.data['note'], 'El proveedor pidió cambiar la fecha.')
        self.assertIsNotNone(completed.data['done_at'])

