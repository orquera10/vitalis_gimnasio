from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from members.models import Member, Plan
from classes.models import Trainer, ClassCategory, ClassSession, ClassBooking
from portal.models import (
    WorkoutRoutine,
    RoutineDay,
    RoutineExercise,
    BodyMetric,
    PersonalRecord,
    MemberActivityDay
)


class PortalViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.plan = Plan.objects.create(
            name="Black Pass VIP",
            price=Decimal("35000.00"),
            duration_days=30
        )
        self.trainer = Trainer.objects.create(
            first_name="Lucas",
            last_name="Torres",
            specialty="Crossfit"
        )
        self.member = Member.objects.create(
            first_name="Martín",
            last_name="Fuentes",
            dni="38492019",
            email="martin.fuentes@vitalis.com",
            plan=self.plan,
            status="ACTIVA"
        )
        self.user = self.member.create_or_sync_user_account()

        self.routine = WorkoutRoutine.objects.create(
            member=self.member,
            name="Hipertrofia Clásica",
            goal="Empuje",
            trainer=self.trainer,
            total_weeks=8,
            current_week=3,
            progress_percent=38
        )
        self.day = RoutineDay.objects.create(
            routine=self.routine,
            day_name="Lunes",
            subtitle="Hipertrofia de Empuje: Pecho y Tríceps",
            order=1
        )
        self.exercise = RoutineExercise.objects.create(
            routine_day=self.day,
            name="Press de Banca Plano",
            muscle_group="Pecho",
            series_reps="4 x 10",
            rest_seconds=90,
            order=1
        )
        self.metric = BodyMetric.objects.create(
            member=self.member,
            date=date(2026, 8, 24),
            weight_kg=Decimal("78.50"),
            body_fat_pct=Decimal("18.2"),
            muscle_mass_kg=Decimal("42.10")
        )
        self.pr = PersonalRecord.objects.create(
            member=self.member,
            exercise_name="Press de Banca Plano",
            weight_kg=Decimal("85.00"),
            achieved_date=date(2026, 8, 12),
            badge_type="fire"
        )
        self.category = ClassCategory.objects.create(name="Crossfit")
        self.session = ClassSession.objects.create(
            category=self.category,
            trainer=self.trainer,
            date=timezone.now().date(),
            start_time="18:00:00",
            end_time="19:00:00",
            capacity=15
        )

        # Login como socio Martín Fuentes
        self.client.login(username='38492019', password='38492019')

    def test_portal_login_page_renders(self):
        self.client.logout()
        url = reverse('portal:login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portal de Socios")
        self.assertContains(response, "DNI / Cédula")

    def test_portal_login_authentication(self):
        self.client.logout()
        url = reverse('portal:login')
        response = self.client.post(url, {
            'username_or_dni': '38492019',
            'password': '38492019'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('portal:home'))

    def test_portal_unauthenticated_redirects_to_portal_login(self):
        self.client.logout()
        url = reverse('portal:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('portal:login'), response.url)

    def test_member_cannot_access_admin_dashboard(self):
        # Socio autenticado intenta entrar al dashboard de la empresa
        response = self.client.get(reverse('core:home'))
        # Debe ser bloqueado y redirigido al portal
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('portal:home'))

    def test_member_cannot_access_members_list(self):
        # Socio autenticado intenta entrar al listado de socios
        response = self.client.get(reverse('members:list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('portal:home'))

    def test_portal_home_dashboard(self):
        url = reverse('portal:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Martín")
        self.assertContains(response, "Press de Banca Plano")
        self.assertContains(response, "Hipertrofia de Empuje")

    def test_portal_routine_view(self):
        url = reverse('portal:routine')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mi Rutina Actual")
        self.assertContains(response, "Press de Banca Plano")
        self.assertContains(response, "Lucas Torres")

    def test_portal_progress_view(self):
        url = reverse('portal:progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis Avances y Métricas")
        self.assertContains(response, "78.5")
        self.assertContains(response, "85")

    def test_portal_profile_view(self):
        url = reverse('portal:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VITALIS VIP")
        self.assertContains(response, "38492019")

    def test_portal_add_metric_post(self):
        url = reverse('portal:add_metric')
        response = self.client.post(url, {
            'date': '2026-08-25',
            'weight_kg': '78.2',
            'body_fat_pct': '18.0',
            'muscle_mass_kg': '42.3',
            'notes': 'Buena semana de entrenamiento'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BodyMetric.objects.filter(member=self.member).count(), 2)

    def test_portal_class_booking_toggle(self):
        url = reverse('portal:book_class_toggle', kwargs={'session_id': self.session.id})
        # 1. Reservar
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ClassBooking.objects.filter(session=self.session, member=self.member).exists())

        # 2. Cancelar
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ClassBooking.objects.filter(session=self.session, member=self.member).exists())
