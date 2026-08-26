from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date
from decimal import Decimal
import json

from members.models import Member, Plan
from classes.models import Trainer, ClassCategory, ClassSession, ClassBooking
from portal.models import (
    WorkoutRoutine,
    RoutineDay,
    RoutineExercise,
    BodyMetric,
    PersonalRecord
)


class ApiEndpointsTestCase(TestCase):
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
            subtitle="Empuje (Pecho/Tríceps)",
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

    def test_api_socio_dashboard(self):
        url = reverse('api:socio_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['member']['name'], "Martín Fuentes")
        self.assertEqual(data['kpis']['streak'], "5 Días")
        self.assertIn("classes_today", data)

    def test_api_socio_routine(self):
        url = reverse('api:socio_routine')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], "Hipertrofia Clásica")
        self.assertEqual(len(data['days']), 1)
        self.assertEqual(data['days'][0]['exercises'][0]['name'], "Press de Banca Plano")

    def test_api_socio_progress_get(self):
        url = reverse('api:socio_progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['current_stats']['weight_kg'], 78.5)
        self.assertEqual(len(data['personal_records']), 1)

    def test_api_socio_progress_post(self):
        url = reverse('api:socio_progress')
        payload = {
            "date": "2026-08-25",
            "weight_kg": 78.0,
            "body_fat_pct": 18.0,
            "muscle_mass_kg": 42.5
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], "success")
        self.assertEqual(data['weight_kg'], 78.0)

    def test_api_socio_class_booking_toggle(self):
        url = reverse('api:socio_class_booking', kwargs={'session_id': self.session.id})
        # 1. Reservar
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['is_booked'])

        # 2. Cancelar
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_booked'])

    def test_api_socio_profile(self):
        url = reverse('api:socio_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['dni'], "38492019")
        self.assertIn("qr_code_token", data)
