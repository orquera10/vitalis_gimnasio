from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel
from members.models import Member
from classes.models import Trainer


class WorkoutRoutine(TimeStampedModel):
    """
    Representa el plan de entrenamiento asignado a un socio.
    """
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="routines",
        verbose_name="Socio"
    )
    name = models.CharField(max_length=150, verbose_name="Nombre de la Rutina", default="Hipertrofia Clásica")
    goal = models.CharField(max_length=200, verbose_name="Objetivo / Especialidad", default="Hipertrofia de Empuje: Pecho y Tríceps")
    total_weeks = models.PositiveIntegerField(default=8, verbose_name="Semanas Totales")
    current_week = models.PositiveIntegerField(default=3, verbose_name="Semana Actual")
    progress_percent = models.PositiveIntegerField(default=38, verbose_name="Progreso General (%)")
    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_routines",
        verbose_name="Entrenador Asignado"
    )
    trainer_notes = models.TextField(
        blank=True,
        verbose_name="Notas y Consejos del Entrenador",
        default="Para este entrenamiento de empuje, enfócate en la fase excéntrica (bajada) en el Press de Banca. Mantén una bajada controlada de 3 segundos para maximizar el reclutamiento de fibras musculares. Si completas todas las series con buena técnica, incrementa 2.5 kg en la última de press inclinado."
    )
    is_active = models.BooleanField(default=True, verbose_name="¿Rutina Activa?")

    class Meta:
        verbose_name = "Rutina de Entrenamiento"
        verbose_name_plural = "Rutinas de Entrenamiento"
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.member.full_name} (Semana {self.current_week}/{self.total_weeks})"


class RoutineDay(TimeStampedModel):
    """
    Día de entrenamiento dentro de una rutina semanal (Lunes, Martes, etc.).
    """
    DAY_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    routine = models.ForeignKey(
        WorkoutRoutine,
        on_delete=models.CASCADE,
        related_name="days",
        verbose_name="Rutina"
    )
    day_name = models.CharField(max_length=20, choices=DAY_CHOICES, verbose_name="Día")
    subtitle = models.CharField(max_length=150, verbose_name="Enfoque / Grupo Muscular", default="Empuje (Pecho/Tríceps)")
    is_rest_day = models.BooleanField(default=False, verbose_name="¿Día de Descanso?")
    order = models.PositiveIntegerField(default=1, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Día de Rutina"
        verbose_name_plural = "Días de Rutina"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.day_name}: {self.subtitle} ({self.routine.name})"


class RoutineExercise(TimeStampedModel):
    """
    Ejercicio individual asignado a un día de entrenamiento.
    """
    routine_day = models.ForeignKey(
        RoutineDay,
        on_delete=models.CASCADE,
        related_name="exercises",
        verbose_name="Día de Rutina"
    )
    name = models.CharField(max_length=150, verbose_name="Nombre del Ejercicio")
    muscle_group = models.CharField(max_length=100, verbose_name="Grupo Muscular", default="Pecho")
    series_reps = models.CharField(max_length=50, verbose_name="Series x Repeticiones", default="4 x 10")
    rest_seconds = models.PositiveIntegerField(default=90, verbose_name="Tiempo de Descanso (Segundos)")
    image_url = models.URLField(
        blank=True,
        default="https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=200&auto=format&fit=crop&q=80",
        verbose_name="URL de Imagen/Demostración"
    )
    order = models.PositiveIntegerField(default=1, verbose_name="Orden")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Notas técnicas")

    class Meta:
        verbose_name = "Ejercicio de Rutina"
        verbose_name_plural = "Ejercicios de Rutina"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.series_reps}) - {self.routine_day.day_name}"


class BodyMetric(TimeStampedModel):
    """
    Registro histórico de mediciones corporales y evolución física del socio.
    """
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="body_metrics",
        verbose_name="Socio"
    )
    date = models.DateField(default=timezone.now, verbose_name="Fecha de Medición")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Peso Corporal (kg)")
    body_fat_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="% Grasa Corporal")
    muscle_mass_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Masa Muscular Estimada (kg)")
    waist_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Cintura (cm)")
    chest_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Pecho (cm)")
    photo_front = models.ImageField(upload_to="metrics/photos/", blank=True, null=True, verbose_name="Foto de Progreso")
    photo_url = models.URLField(blank=True, verbose_name="URL Foto Progreso")
    notes = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Medición Corporal"
        verbose_name_plural = "Mediciones Corporales"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.member.full_name} - {self.weight_kg}kg ({self.date.strftime('%d/%m/%Y')})"


class PersonalRecord(TimeStampedModel):
    """
    Récord personal (PR) o marca máxima de fuerza del socio.
    """
    BADGE_CHOICES = [
        ('fire', 'Fuego 🔥'),
        ('crown', 'Corona 👑'),
        ('bolt', 'Rayo ⚡'),
        ('star', 'Estrella ⭐'),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="personal_records",
        verbose_name="Socio"
    )
    exercise_name = models.CharField(max_length=150, verbose_name="Ejercicio")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Peso Logrado (kg)")
    achieved_date = models.DateField(default=timezone.now, verbose_name="Fecha Logrado")
    badge_type = models.CharField(max_length=20, choices=BADGE_CHOICES, default='fire', verbose_name="Insignia / Icono")
    order = models.PositiveIntegerField(default=1, verbose_name="Orden")

    class Meta:
        verbose_name = "Récord Personal (PR)"
        verbose_name_plural = "Récords Personales (PRs)"
        ordering = ['order', '-weight_kg']

    def __str__(self):
        return f"{self.exercise_name}: {self.weight_kg}kg - {self.member.full_name}"


class MemberActivityDay(TimeStampedModel):
    """
    Registro diario de asistencia o descanso del socio para el calendario semanal.
    """
    STATUS_CHOICES = [
        ('ENTRENADO', 'Entrenado'),
        ('DESCANSO', 'Descanso'),
        ('PENDIENTE', 'Pendiente'),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="activity_days",
        verbose_name="Socio"
    )
    date = models.DateField(verbose_name="Fecha")
    day_name = models.CharField(max_length=20, verbose_name="Día de la Semana")
    day_number = models.PositiveIntegerField(verbose_name="Número de Día")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ENTRENADO', verbose_name="Estado")

    class Meta:
        verbose_name = "Actividad Diaria"
        verbose_name_plural = "Actividades Diarias"
        unique_together = ('member', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.member.full_name} - {self.day_name} {self.day_number}: {self.status}"
