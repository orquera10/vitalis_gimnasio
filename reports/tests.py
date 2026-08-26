from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from members.models import Member, Plan
from classes.models import Trainer, ClassCategory, ClassSchedule, ClassSession, ClassBooking
from payments.models import Payment


class ReportsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin_reports',
            password='TestPassword123!',
            email='reports@vitalis.com'
        )

        self.plan = Plan.objects.create(
            name="Plan Anual VIP",
            price=Decimal('120000.00'),
            duration_days=365,
            color="#f5b82e"
        )

        self.member = Member.objects.create(
            first_name="Gonzalo",
            last_name="Perez",
            dni="15.888.777-2",
            email="gonzalo@email.com",
            plan=self.plan,
            status="ACTIVA",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=10)
        )

        self.payment = Payment.objects.create(
            member=self.member,
            plan=self.plan,
            amount=Decimal('120000.00'),
            payment_method='MERCADOPAGO',
            status='COMPLETADO',
            payment_date=timezone.now().date()
        )

        self.trainer = Trainer.objects.create(
            first_name="Esteban",
            last_name="Quilodran",
            specialty="Crossfit",
            is_active=True
        )

        self.category = ClassCategory.objects.create(
            name="Crossfit WOD",
            color="#f5b82e"
        )

        self.session = ClassSession.objects.create(
            category=self.category,
            trainer=self.trainer,
            title="WOD de Fuerza",
            date=timezone.now().date(),
            start_time="10:00:00",
            end_time="11:00:00",
            capacity=15,
            room="Box 1"
        )

        self.booking = ClassBooking.objects.create(
            session=self.session,
            member=self.member,
            status="PRESENTE"
        )

    def test_reports_dashboard_unauthenticated_redirect(self):
        """Usuario anónimo es redirigido a login."""
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response.url)

    def test_reports_dashboard_authenticated(self):
        """Dashboard de reportes calcula KPIs y renderiza con éxito."""
        self.client.login(username='admin_reports', password='TestPassword123!')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/dashboard.html')
        self.assertContains(response, "120000")
        self.assertContains(response, "Gonzalo Perez")
        self.assertContains(response, "Crossfit WOD")

    def test_export_payments_csv(self):
        """Descarga de archivo CSV de pagos con cabeceras y datos válidos."""
        self.client.login(username='admin_reports', password='TestPassword123!')
        url = reverse('reports:export_payments_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="reporte_pagos_vitalis_', response['Content-Disposition'])
        content = response.content.decode('utf-8-sig')
        self.assertIn(self.payment.invoice_number, content)
        self.assertIn("Gonzalo Perez", content)
        self.assertIn("120000.00", content)

    def test_export_members_csv(self):
        """Descarga de archivo CSV de socios."""
        self.client.login(username='admin_reports', password='TestPassword123!')
        url = reverse('reports:export_members_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8-sig')
        self.assertIn("Gonzalo", content)
        self.assertIn("15.888.777-2", content)
        self.assertIn("Plan Anual VIP", content)

    def test_export_attendance_csv(self):
        """Descarga de archivo CSV de asistencias."""
        self.client.login(username='admin_reports', password='TestPassword123!')
        url = reverse('reports:export_attendance_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8-sig')
        self.assertIn("WOD de Fuerza", content)
        self.assertIn("Gonzalo Perez", content)
        self.assertIn("Presente", content)

    def test_printable_executive_report(self):
        """Vista de informe ejecutivo formal para PDF/Impresión."""
        self.client.login(username='admin_reports', password='TestPassword123!')
        url = reverse('reports:printable')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/printable_report.html')
        self.assertContains(response, "Informe Ejecutivo Mensual")
        self.assertContains(response, "VITALIS")
