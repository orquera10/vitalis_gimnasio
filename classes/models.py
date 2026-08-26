from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel


class Trainer(TimeStampedModel):
    """
    Representa un entrenador o instructor del gimnasio.
    """
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    specialty = models.CharField(max_length=150, verbose_name="Especialidad / Disciplinas")
    email = models.EmailField(blank=True, verbose_name="Correo Electrónico")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono / WhatsApp")
    avatar_file = models.ImageField(
        upload_to='avatars/trainers/',
        blank=True,
        null=True,
        verbose_name="Foto de Perfil (Archivo)"
    )
    avatar = models.URLField(
        blank=True,
        default="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80",
        verbose_name="Foto / Avatar (URL alternativa)"
    )
    bio = models.TextField(blank=True, verbose_name="Biografía / Certificaciones")
    is_active = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Entrenador"
        verbose_name_plural = "Entrenadores"
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.specialty})"

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
        return "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"


class ClassCategory(TimeStampedModel):
    """
    Disciplina o tipo de entrenamiento (Funcional, Crossfit, Yoga, Spinning, etc.).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Disciplina")
    color = models.CharField(max_length=20, default="#f5b82e", verbose_name="Color de Identificación (HEX)")
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, default="dumbbell", verbose_name="Identificador de Icono")

    class Meta:
        verbose_name = "Disciplina / Categoría"
        verbose_name_plural = "Disciplinas / Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name


class ClassSchedule(TimeStampedModel):
    """
    Regla de horario recurrente para una clase (ej. Funcional los miércoles y viernes de 20:00 a 22:00).
    """
    DAY_CHOICES = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]

    title = models.CharField(max_length=120, verbose_name="Título de la Clase")
    category = models.ForeignKey(ClassCategory, on_delete=models.CASCADE, related_name="schedules", verbose_name="Disciplina")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="schedules", verbose_name="Entrenador")
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES, verbose_name="Día de la Semana")
    start_time = models.TimeField(verbose_name="Hora de Inicio")
    end_time = models.TimeField(verbose_name="Hora de Fin")
    room = models.CharField(max_length=100, default="Sala Principal", verbose_name="Salón / Box")
    capacity = models.PositiveIntegerField(default=20, verbose_name="Cupo Máximo")
    is_active = models.BooleanField(default=True, verbose_name="¿Horario Activo?")

    class Meta:
        verbose_name = "Horario Recurrente de Clase"
        verbose_name_plural = "Horarios Recurrentes de Clases"
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.title} ({self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

    @property
    def day_name(self):
        return self.get_day_of_week_display()


class ClassSession(TimeStampedModel):
    """
    Sesión o clase puntual en una fecha específica en el almanaque.
    """
    STATUS_CHOICES = [
        ('PROGRAMADA', 'Programada'),
        ('EN_CURSO', 'En Curso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    schedule = models.ForeignKey(ClassSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    title = models.CharField(max_length=120, verbose_name="Nombre de la Clase")
    category = models.ForeignKey(ClassCategory, on_delete=models.CASCADE, related_name="sessions", verbose_name="Disciplina")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="sessions", verbose_name="Entrenador")
    date = models.DateField(default=timezone.now, verbose_name="Fecha")
    start_time = models.TimeField(verbose_name="Hora de Inicio")
    end_time = models.TimeField(verbose_name="Hora de Fin")
    room = models.CharField(max_length=100, default="Sala Principal", verbose_name="Salón / Box")
    capacity = models.PositiveIntegerField(default=20, verbose_name="Cupo Total")
    booked_count = models.PositiveIntegerField(default=0, verbose_name="Cupos Reservados")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PROGRAMADA', verbose_name="Estado")

    class Meta:
        verbose_name = "Sesión de Clase"
        verbose_name_plural = "Sesiones de Clases"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} - {self.date.strftime('%d/%m/%Y')} {self.start_time.strftime('%H:%M')}"

    @property
    def available_spots(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_full(self):
        return self.booked_count >= self.capacity

    @property
    def time_range(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    def recalculate_booked_count(self):
        """
        Recalcula y actualiza los cupos reservados según las inscripciones activas.
        """
        count = self.bookings.exclude(status='CANCELADO').count()
        self.booked_count = count
        self.save(update_fields=['booked_count'])
        return count


class ClassBooking(TimeStampedModel):
    """
    Inscripción o reserva de un socio a una sesión puntual de clase.
    """
    STATUS_CHOICES = [
        ('RESERVADO', 'Reservado'),
        ('PRESENTE', 'Presente'),
        ('AUSENTE', 'Ausente'),
        ('CANCELADO', 'Cancelado'),
    ]

    session = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Sesión de Clase"
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name="class_bookings",
        verbose_name="Socio / Miembro"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='RESERVADO',
        verbose_name="Estado de Asistencia"
    )
    booking_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Inscripción")
    notes = models.TextField(blank=True, verbose_name="Notas / Observaciones")

    class Meta:
        verbose_name = "Inscripción a Clase"
        verbose_name_plural = "Inscripciones a Clases"
        ordering = ['-booking_date']
        constraints = [
            models.UniqueConstraint(fields=['session', 'member'], name='unique_session_member_booking')
        ]

    def __str__(self):
        return f"{self.member.full_name} -> {self.session.title} ({self.get_status_display()})"

    @property
    def status_badge_class(self):
        mapping = {
            'RESERVADO': 'badge-warning',
            'PRESENTE': 'badge-success',
            'AUSENTE': 'badge-danger',
            'CANCELADO': 'badge-secondary',
        }
        return mapping.get(self.status, 'badge-info')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.session.recalculate_booked_count()

    def delete(self, *args, **kwargs):
        session = self.session
        super().delete(*args, **kwargs)
        session.recalculate_booked_count()
