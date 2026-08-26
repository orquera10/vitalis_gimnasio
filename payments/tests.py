from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from members.models import Member, Plan
from payments.models import Payment


class PaymentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin_payments',
            password='TestPassword123!',
            email='payments@vitalis.com'
        )
        
        self.plan = Plan.objects.create(
            name="Plan Premium Semestral",
            price=Decimal('180000.00'),
            duration_days=180,
            color="#f5b82e"
        )
        
        self.member = Member.objects.create(
            first_name="Camila",
            last_name="Torres",
            dni="17.999.888-1",
            email="camila.torres@ejemplo.com",
            phone="+56 9 7777 8888",
            plan=self.plan,
            status="ACTIVA",
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() - timedelta(days=1)  # Vencido ayer
        )

    def test_payment_creation_and_auto_invoice_number(self):
        """Verifica que al guardar un pago se genere automáticamente un número de recibo secuencial."""
        payment = Payment.objects.create(
            member=self.member,
            plan=self.plan,
            amount=Decimal('180000.00'),
            payment_method='MERCADOPAGO',
            status='COMPLETADO',
            notes='Pago QR'
        )
        self.assertTrue(payment.invoice_number.startswith(f"REC-{timezone.now().year}-"))
        self.assertEqual(payment.status_badge_class, 'badge-success')
        self.assertEqual(payment.method_icon, '📱')

    def test_payment_auto_renews_membership(self):
        """Un pago completado con auto_renew_membership debe extender la fecha fin del socio y ponerlo en ACTIVA."""
        today = timezone.now().date()
        payment = Payment.objects.create(
            member=self.member,
            plan=self.plan,
            amount=Decimal('180000.00'),
            payment_method='TRANSFERENCIA',
            status='COMPLETADO',
            auto_renew_membership=True,
            payment_date=today
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.status, 'ACTIVA')
        expected_end_date = today + timedelta(days=180)
        self.assertEqual(self.member.end_date, expected_end_date)

    def test_payment_list_unauthenticated_redirect(self):
        """Un usuario sin sesión es redirigido al login."""
        response = self.client.get(reverse('payments:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response.url)

    def test_payment_list_view_authenticated(self):
        """Listado de pagos con métricas KPI y búsqueda."""
        self.client.login(username='admin_payments', password='TestPassword123!')
        payment = Payment.objects.create(
            member=self.member,
            plan=self.plan,
            amount=Decimal('180000.00'),
            payment_method='TARJETA_CREDITO',
            status='COMPLETADO'
        )
        response = self.client.get(reverse('payments:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/payment_list.html')
        self.assertContains(response, payment.invoice_number)
        self.assertContains(response, "Camila Torres")

    def test_payment_create_view(self):
        """Registro de nuevo cobro a través del formulario."""
        self.client.login(username='admin_payments', password='TestPassword123!')
        url = reverse('payments:create')
        response = self.client.post(url, {
            'member': self.member.pk,
            'plan': self.plan.pk,
            'amount': '180000.00',
            'payment_method': 'EFECTIVO',
            'status': 'COMPLETADO',
            'payment_date': timezone.now().date().strftime('%Y-%m-%d'),
            'auto_renew_membership': True,
            'notes': 'Cobro en ventanilla'
        })
        self.assertEqual(response.status_code, 302)
        new_payment = Payment.objects.filter(member=self.member, payment_method='EFECTIVO').first()
        self.assertIsNotNone(new_payment)
        self.assertEqual(new_payment.amount, Decimal('180000.00'))

    def test_payment_detail_receipt_view(self):
        """Ficha de recibo digital oficial."""
        self.client.login(username='admin_payments', password='TestPassword123!')
        payment = Payment.objects.create(
            member=self.member,
            plan=self.plan,
            amount=Decimal('180000.00'),
            payment_method='TRANSFERENCIA',
            status='COMPLETADO'
        )
        url = reverse('payments:detail', args=[payment.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/payment_detail.html')
        self.assertContains(response, payment.invoice_number)
        self.assertContains(response, "VITALIS")
        self.assertContains(response, "Camila Torres")

    def test_payment_cancel_view(self):
        """Anulación de un pago existente."""
        self.client.login(username='admin_payments', password='TestPassword123!')
        payment = Payment.objects.create(
            member=self.member,
            plan=self.plan,
            amount=Decimal('180000.00'),
            payment_method='EFECTIVO',
            status='COMPLETADO'
        )
        url = reverse('payments:cancel', args=[payment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'ANULADO')
