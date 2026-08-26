from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from core.models import TimeStampedModel


class Plan(TimeStampedModel):
    """
    Representa un plan o membresía disponible en Vitalis Fitness.
    """
    name = models.CharField(max_length=100, verbose_name="Nombre del Plan")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ($)")
    duration_days = models.PositiveIntegerField(default=30, verbose_name="Duración (días)")
    color = models.CharField(max_length=20, default="#f5b82e", verbose_name="Color Distintivo (HEX)")
    description = models.TextField(blank=True, verbose_name="Descripción / Beneficios")
    is_active = models.BooleanField(default=True, verbose_name="¿Activo para venta?")

    class Meta:
        verbose_name = "Plan de Membresía"
        verbose_name_plural = "Planes de Membresía"
        ordering = ['-price']

    def __str__(self):
        return f"{self.name} - ${self.price}"


class Member(TimeStampedModel):
    """
    Representa un socio / cliente registrado en el gimnasio.
    """
    STATUS_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('PENDIENTE', 'Pendiente'),
        ('VENCIDO', 'Vencido'),
        ('INACTIVA', 'Inactiva'),
    ]

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro / Prefiero no decir'),
    ]

    # Cuenta de Usuario vinculada para acceso al Portal de Socios / App Móvil
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profile',
        verbose_name="Cuenta de Usuario Portal"
    )

    # Datos Personales
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI / Cédula")
    email = models.EmailField(verbose_name="Correo Electrónico")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono / WhatsApp")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M', verbose_name="Género")
    address = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    avatar_file = models.ImageField(
        upload_to='avatars/members/',
        blank=True,
        null=True,
        verbose_name="Foto de Perfil (Archivo)"
    )
    avatar = models.URLField(
        blank=True,
        default="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
        verbose_name="Foto / Avatar (URL alternativa)"
    )

    # Membresía y Plan
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="members",
        verbose_name="Plan Contratado"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='ACTIVA',
        verbose_name="Estado de Membresía"
    )
    start_date = models.DateField(default=timezone.now, verbose_name="Fecha de Inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Vencimiento")

    # Información de Emergencia y Médica
    emergency_contact_name = models.CharField(max_length=100, blank=True, verbose_name="Contacto de Emergencia")
    emergency_contact_phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono de Emergencia")
    medical_notes = models.TextField(blank=True, verbose_name="Observaciones Médicas / Físicas")

    class Meta:
        verbose_name = "Socio / Miembro"
        verbose_name_plural = "Socios / Miembros"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.dni})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def avatar_url(self):
        if self.avatar_file:
            try:
                return self.avatar_file.url
            except ValueError:
                pass
        if self.avatar:
            return self.avatar
        return "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80"

    @property
    def status_badge_class(self):
        mapping = {
            'ACTIVA': 'badge-success',
            'PENDIENTE': 'badge-warning',
            'VENCIDO': 'badge-danger',
            'INACTIVA': 'badge-secondary',
        }
        return mapping.get(self.status, 'badge-info')

    def create_or_sync_user_account(self, default_password=None):
        """
        Crea o sincroniza la cuenta de usuario de Django para que el socio pueda ingresar al portal.
        """
        username = self.dni.strip().replace('.', '').replace('-', '')
        password = default_password or username

        user = self.user
        if not user:
            # Buscar por username existente o crear nuevo
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=self.email,
                    password=password,
                    first_name=self.first_name,
                    last_name=self.last_name
                )
            else:
                user.email = self.email
                user.first_name = self.first_name
                user.last_name = self.last_name
                if default_password:
                    user.set_password(default_password)
                user.save()
            self.user = user
            self.save(update_fields=['user'])
        else:
            # Actualizar datos
            user.username = username
            user.email = self.email
            user.first_name = self.first_name
            user.last_name = self.last_name
            if default_password:
                user.set_password(default_password)
            user.save()

        return user

    def assign_default_routine_if_none(self):
        """
        Si el socio no tiene una rutina asignada, le crea una rutina de adaptación inicial.
        """
        try:
            from portal.models import WorkoutRoutine, RoutineDay, RoutineExercise
            if not self.routines.filter(is_active=True).exists():
                routine = WorkoutRoutine.objects.create(
                    member=self,
                    name="Adaptación y Acondicionamiento",
                    goal="Acondicionamiento General & Fuerza",
                    total_weeks=6,
                    current_week=1,
                    progress_percent=15,
                    trainer_notes="¡Bienvenido a Vitalis! Esta rutina inicial de adaptación te permitirá preparar articulaciones y músculos. Enfócate en la técnica antes de subir cargas.",
                    is_active=True
                )
                # Días básicos
                day1 = RoutineDay.objects.create(routine=routine, day_name="Lunes", subtitle="Fullbody A (Fuerza & Core)", order=1)
                day2 = RoutineDay.objects.create(routine=routine, day_name="Miércoles", subtitle="Fullbody B (Resistencia)", order=2)
                day3 = RoutineDay.objects.create(routine=routine, day_name="Viernes", subtitle="Fullbody C (Funcional)", order=3)

                # Ejercicios básicos
                RoutineExercise.objects.create(routine_day=day1, name="Sentadilla con Mancuerna", muscle_group="Piernas", series_reps="3 x 12", rest_seconds=60, order=1)
                RoutineExercise.objects.create(routine_day=day1, name="Press de Banca con Mancuernas", muscle_group="Pecho", series_reps="3 x 10", rest_seconds=60, order=2)
                RoutineExercise.objects.create(routine_day=day1, name="Jalón al Pecho en Polea", muscle_group="Espalda", series_reps="3 x 12", rest_seconds=60, order=3)
                RoutineExercise.objects.create(routine_day=day1, name="Plancha Abdominal", muscle_group="Core", series_reps="3 x 30s", rest_seconds=45, order=4)
        except Exception:
            pass

    def save(self, *args, **kwargs):
        # Calcular automáticamente la fecha de fin si no se especificó y tiene un plan asignado
        if not self.end_date and self.plan and self.start_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)


class MemberCheckIn(TimeStampedModel):
    """
    Registro histórico de accesos y asistencias al gimnasio mediante el terminal de entrada / kiosko.
    """
    ACCESS_STATUS_CHOICES = [
        ('PERMITIDO', 'Acceso Permitido (Al día)'),
        ('VENCIDO', 'Acceso Denegado (Membresía Vencida)'),
        ('PENDIENTE', 'Acceso Denegado (Pago Pendiente)'),
        ('INACTIVO', 'Acceso Denegado (Socio Inactivo)'),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='checkins',
        verbose_name="Socio"
    )
    status = models.CharField(
        max_length=20,
        choices=ACCESS_STATUS_CHOICES,
        default='PERMITIDO',
        verbose_name="Estado de Acceso"
    )
    checkin_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de Acceso"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Observaciones / Mensaje"
    )

    class Meta:
        verbose_name = "Registro de Acceso / Check-in"
        verbose_name_plural = "Registros de Acceso / Check-ins"
        ordering = ['-checkin_time']

    def __str__(self):
        return f"{self.member.full_name} - {self.get_status_display()} ({self.checkin_time.strftime('%d/%m/%Y %H:%M')})"
