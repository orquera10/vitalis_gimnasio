from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import TimeStampedModel


class Payment(TimeStampedModel):
    """
    Representa una transacción de pago o cobro de membresía en Vitalis Fitness.
    """
    METHOD_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria / QR'),
        ('TARJETA_DEBITO', 'Tarjeta de Débito'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('MERCADOPAGO', 'Mercado Pago'),
    ]

    STATUS_CHOICES = [
        ('COMPLETADO', 'Completado'),
        ('PENDIENTE', 'Pendiente'),
        ('ANULADO', 'Anulado / Reembolsado'),
    ]

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Socio / Cliente"
    )
    plan = models.ForeignKey(
        'members.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Plan / Membresía"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto Abonado ($)"
    )
    payment_method = models.CharField(
        max_length=25,
        choices=METHOD_CHOICES,
        default='EFECTIVO',
        verbose_name="Método de Pago"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='COMPLETADO',
        verbose_name="Estado del Pago"
    )
    payment_date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Pago"
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="N° de Comprobante / Recibo"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas / Referencia de Transacción"
    )
    auto_renew_membership = models.BooleanField(
        default=True,
        verbose_name="¿Extender / Activar Membresía Automáticamente?"
    )

    class Meta:
        verbose_name = "Pago / Cobranza"
        verbose_name_plural = "Pagos y Cobranzas"
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.invoice_number or 'Pago'} - {self.member.full_name} (${self.amount})"

    @property
    def status_badge_class(self):
        mapping = {
            'COMPLETADO': 'badge-success',
            'PENDIENTE': 'badge-warning',
            'ANULADO': 'badge-danger',
        }
        return mapping.get(self.status, 'badge-info')

    @property
    def method_icon(self):
        mapping = {
            'EFECTIVO': '💵',
            'TRANSFERENCIA': '🏦',
            'TARJETA_DEBITO': '💳',
            'TARJETA_CREDITO': '💳',
            'MERCADOPAGO': '📱',
        }
        return mapping.get(self.payment_method, '💰')

    def generate_invoice_number(self):
        """
        Genera un número de comprobante secuencial único (ej. REC-2026-0001).
        """
        current_year = timezone.now().year
        last_payment = Payment.objects.filter(
            invoice_number__startswith=f"REC-{current_year}-"
        ).order_by('-id').first()

        if last_payment and last_payment.invoice_number:
            try:
                seq_num = int(last_payment.invoice_number.split('-')[-1]) + 1
            except ValueError:
                seq_num = Payment.objects.count() + 1
        else:
            seq_num = 1

        return f"REC-{current_year}-{seq_num:04d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        super().save(*args, **kwargs)

        # Si el pago está completado y se solicita renovar la membresía del socio
        if self.status == 'COMPLETADO' and self.auto_renew_membership and self.member:
            member = self.member
            if self.plan:
                member.plan = self.plan
                duration = self.plan.duration_days
            elif member.plan:
                duration = member.plan.duration_days
            else:
                duration = 30

            # Calcular nueva fecha de vencimiento
            today = timezone.now().date()
            if member.end_date and member.end_date >= today:
                member.end_date = member.end_date + timedelta(days=duration)
            else:
                member.start_date = self.payment_date
                member.end_date = self.payment_date + timedelta(days=duration)

            member.status = 'ACTIVA'
            member.save(update_fields=['plan', 'start_date', 'end_date', 'status'])
