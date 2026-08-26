from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from members.models import Member, Plan
from payments.models import Payment


class Command(BaseCommand):
    help = 'Puebla la base de datos con pagos y cobros de ejemplo.'

    def handle(self, *args, **options):
        self.stdout.write("Generando pagos y transacciones de prueba...")

        members = list(Member.objects.all())
        if not members:
            self.stdout.write(self.style.WARNING("No hay socios registrados. Ejecuta primero seed_members."))
            return

        plans = list(Plan.objects.all())
        today = timezone.now().date()

        # Generar pagos recientes
        sample_payments_data = [
            {
                'member_index': 0,
                'plan_index': 0 if plans else None,
                'days_ago': 2,
                'method': 'MERCADOPAGO',
                'status': 'COMPLETADO',
                'notes': 'Pago aprobado vía Mercado Pago QR. Ref #MP-883912.',
            },
            {
                'member_index': 1 % len(members),
                'plan_index': 1 % len(plans) if len(plans) > 1 else None,
                'days_ago': 5,
                'method': 'TRANSFERENCIA',
                'status': 'COMPLETADO',
                'notes': 'Transferencia bancaria Banco Santander comprobante #9482.',
            },
            {
                'member_index': 2 % len(members),
                'plan_index': 0 if plans else None,
                'days_ago': 10,
                'method': 'TARJETA_CREDITO',
                'status': 'COMPLETADO',
                'notes': 'Cobro POS terminal en recepción. Visa Débito.',
            },
            {
                'member_index': 0,
                'plan_index': None,
                'days_ago': 1,
                'method': 'EFECTIVO',
                'status': 'PENDIENTE',
                'notes': 'Seña de reserva pendiente de completar en recepción.',
            },
            {
                'member_index': min(3, len(members) - 1),
                'plan_index': 0 if plans else None,
                'days_ago': 18,
                'method': 'EFECTIVO',
                'status': 'COMPLETADO',
                'notes': 'Pago en efectivo abonado en recepción.',
            }
        ]

        count = 0
        for data in sample_payments_data:
            member = members[data['member_index']]
            plan = plans[data['plan_index']] if data['plan_index'] is not None and plans else member.plan
            amount = plan.price if plan else Decimal('35000.00')
            payment_date = today - timedelta(days=data['days_ago'])

            # Evitar duplicados por fecha y socio
            if not Payment.objects.filter(member=member, payment_date=payment_date, amount=amount).exists():
                payment = Payment(
                    member=member,
                    plan=plan,
                    amount=amount,
                    payment_method=data['method'],
                    status=data['status'],
                    payment_date=payment_date,
                    notes=data['notes'],
                    auto_renew_membership=(data['status'] == 'COMPLETADO')
                )
                payment.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Se crearon {count} pagos de prueba exitosamente."))
