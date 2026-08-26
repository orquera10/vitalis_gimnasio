from django.db import models


class TimeStampedModel(models.Model):
    """
    Modelo base abstracto que provee campos de auditoría de fecha
    de creación y última actualización para ser heredado en otros módulos del gimnasio.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        abstract = True


class GymSetting(TimeStampedModel):
    """
    Configuración general, perfil de la sede, datos de facturación y reglas del gimnasio.
    """
    gym_name = models.CharField(max_length=150, default="Vitalis Fitness Club", verbose_name="Nombre del Gimnasio")
    branch_name = models.CharField(max_length=150, default="Sede Central • Palermo Soho", verbose_name="Nombre de la Sede")
    tax_id = models.CharField(max_length=50, default="30-71829304-5", verbose_name="CUIT / Identificación Fiscal")
    address = models.CharField(max_length=255, default="Av. del Libertador 4500, Palermo, CABA", verbose_name="Dirección")
    phone = models.CharField(max_length=50, default="+54 11 4899-2030", verbose_name="Teléfono")
    whatsapp = models.CharField(max_length=50, default="+54 9 11 5500-8822", verbose_name="WhatsApp de Recepción")
    email = models.EmailField(default="contacto@vitalisfitness.com", verbose_name="Email Oficial")
    bank_cbu = models.CharField(max_length=100, default="0000003100045678912345", verbose_name="CBU / CVU Bancario")
    bank_alias = models.CharField(max_length=100, default="VITALIS.FITNESS.PAGO", verbose_name="Alias Bancario / Mercado Pago")
    receipt_footer = models.TextField(
        default="Gracias por elegir Vitalis Fitness Club. Las cuotas abonadas son personales y no reembolsables.",
        verbose_name="Mensaje de Pie de Recibo"
    )
    # Reglas de negocio
    days_advance_notice = models.PositiveIntegerField(default=7, verbose_name="Días de Anticipación para Alerta de Vencimiento")
    grace_period_days = models.PositiveIntegerField(default=3, verbose_name="Días de Gracia para Acceso tras Vencimiento")
    default_class_capacity = models.PositiveIntegerField(default=15, verbose_name="Capacidad por Defecto en Clases")

    class Meta:
        verbose_name = "Configuración del Gimnasio"
        verbose_name_plural = "Configuraciones del Gimnasio"

    def __str__(self):
        return f"{self.gym_name} ({self.branch_name})"

    @classmethod
    def get_settings(cls):
        setting, _ = cls.objects.get_or_create(id=1)
        return setting

