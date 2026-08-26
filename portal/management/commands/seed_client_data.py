from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
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


class Command(BaseCommand):
    help = "Siembra datos completos para el portal de clientes (Socio Martín Fuentes y rutinas, métricas, PRs y clases)."

    def handle(self, *args, **options):
        self.stdout.write("Iniciando sembrado de datos para el Portal de Socios...")

        # 1. Asegurar Plan Black Pass VIP
        plan_vip, _ = Plan.objects.get_or_create(
            name="Black Pass VIP",
            defaults={
                "price": Decimal("35000.00"),
                "duration_days": 30,
                "color": "#f5b82e",
                "description": "Acceso total ilimitado a todas las sedes, disciplinas, zona VIP, toallas y vestuarios ejecutivos.",
                "is_active": True
            }
        )

        # 2. Asegurar Entrenador Lucas Torres
        trainer_lucas, _ = Trainer.objects.get_or_create(
            first_name="Lucas",
            last_name="Torres",
            defaults={
                "specialty": "Crossfit & Hipertrofia",
                "email": "lucas.torres@vitalis.com",
                "phone": "+54 9 11 5544-3322",
                "avatar": "https://images.unsplash.com/photo-1568602471122-7832951cc4c5?w=120&auto=format&fit=crop&q=80",
                "bio": "Especialista en biomecánica aplicada y entrenamiento de fuerza de alta intensidad."
            }
        )

        trainer_mario, _ = Trainer.objects.get_or_create(
            first_name="Mario",
            last_name="Ruiz",
            defaults={
                "specialty": "Spinning & Cardio Pro",
                "email": "mario.ruiz@vitalis.com",
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80"
            }
        )

        trainer_ana, _ = Trainer.objects.get_or_create(
            first_name="Ana",
            last_name="Sofía",
            defaults={
                "specialty": "Power Yoga & Flexibilidad",
                "email": "ana.sofia@vitalis.com",
                "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"
            }
        )

        # 3. Crear / Actualizar Socio Martín Fuentes
        member_martin, created = Member.objects.get_or_create(
            dni="38492019",
            defaults={
                "first_name": "Martín",
                "last_name": "Fuentes",
                "email": "martin.fuentes@vitalis.com",
                "phone": "+54 9 11 4829-1928",
                "plan": plan_vip,
                "status": "ACTIVA",
                "start_date": timezone.now().date() - timedelta(days=15),
                "end_date": timezone.now().date() + timedelta(days=15),
                "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80",
                "emergency_contact_name": "Laura Fuentes",
                "emergency_contact_phone": "+54 9 11 4433-2211",
                "medical_notes": "Apto médico al día presentado en Julio 2026."
            }
        )

        # 4. Crear Usuario para login de Martín
        user_martin, user_created = User.objects.get_or_create(
            username="martinfuentes",
            defaults={
                "first_name": "Martín",
                "last_name": "Fuentes",
                "email": "martin.fuentes@vitalis.com",
                "is_staff": False,
                "is_superuser": False
            }
        )
        user_martin.set_password("martin123")
        user_martin.save()

        # También asegurar que el superusuario 'admin' tenga contraseña conocida
        if User.objects.filter(username="admin").exists():
            u = User.objects.get(username="admin")
            u.set_password("admin123")
            u.save()

        # 5. Rutina de Entrenamiento
        WorkoutRoutine.objects.filter(member=member_martin).delete()
        routine = WorkoutRoutine.objects.create(
            member=member_martin,
            name="Hipertrofia Clásica",
            goal="Hipertrofia de Empuje: Pecho y Tríceps",
            total_weeks=8,
            current_week=3,
            progress_percent=38,
            trainer=trainer_lucas,
            trainer_notes="Para este entrenamiento de empuje, enfócate en la fase excéntrica (bajada) en el Press de Banca. Mantén una bajada controlada de 3 segundos para maximizar el reclutamiento de fibras musculares. Si completas todas las series con buena técnica, incrementa 2.5 kg en la última de press inclinado.",
            is_active=True
        )

        # Días de Rutina
        day_lunes = RoutineDay.objects.create(
            routine=routine,
            day_name="Lunes",
            subtitle="Empuje (Pecho/Tríceps)",
            is_rest_day=False,
            order=1
        )
        day_martes = RoutineDay.objects.create(
            routine=routine,
            day_name="Martes",
            subtitle="Tracción (Espalda/Bíceps)",
            is_rest_day=False,
            order=2
        )
        day_miercoles = RoutineDay.objects.create(
            routine=routine,
            day_name="Miércoles",
            subtitle="Pierna Completa",
            is_rest_day=False,
            order=3
        )
        day_jueves = RoutineDay.objects.create(
            routine=routine,
            day_name="Jueves",
            subtitle="Hombros y Brazos",
            is_rest_day=False,
            order=4
        )
        day_viernes = RoutineDay.objects.create(
            routine=routine,
            day_name="Viernes",
            subtitle="Fullbody / Funcional",
            is_rest_day=False,
            order=5
        )

        # Ejercicios para el Lunes
        exercises_lunes = [
            ("Press de Banca Plano", "Pecho", "4 x 10", 90, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=300&auto=format&fit=crop&q=80", 1),
            ("Aperturas con Mancuernas", "Pecho", "3 x 12", 60, "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop&q=80", 2),
            ("Press Inclinado con Mancuernas", "Pecho", "4 x 8", 90, "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=300&auto=format&fit=crop&q=80", 3),
            ("Fondos en Paralelas", "Tríceps / Pecho", "3 x 12", 60, "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=300&auto=format&fit=crop&q=80", 4),
            ("Extensión de Tríceps en Polea", "Tríceps", "3 x 15", 45, "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300&auto=format&fit=crop&q=80", 5),
        ]
        for name, mg, sr, rest, img, ord_num in exercises_lunes:
            RoutineExercise.objects.create(
                routine_day=day_lunes,
                name=name,
                muscle_group=mg,
                series_reps=sr,
                rest_seconds=rest,
                image_url=img,
                order=ord_num
            )

        # Ejercicios para el Martes
        exercises_martes = [
            ("Jalón al Pecho en Polea", "Espalda", "4 x 10", 90, "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop&q=80", 1),
            ("Remo con Barra T", "Espalda", "4 x 8", 90, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=300&auto=format&fit=crop&q=80", 2),
            ("Curl de Bíceps con Barra Z", "Bíceps", "3 x 12", 60, "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=300&auto=format&fit=crop&q=80", 3),
            ("Curl Martillo en Banco Inclinado", "Bíceps", "3 x 12", 60, "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300&auto=format&fit=crop&q=80", 4),
        ]
        for name, mg, sr, rest, img, ord_num in exercises_martes:
            RoutineExercise.objects.create(
                routine_day=day_martes,
                name=name,
                muscle_group=mg,
                series_reps=sr,
                rest_seconds=rest,
                image_url=img,
                order=ord_num
            )

        # Ejercicios para el Miércoles
        exercises_miercoles = [
            ("Sentadilla Trasera con Barra", "Cuádriceps", "4 x 8", 120, "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=300&auto=format&fit=crop&q=80", 1),
            ("Prensa de Piernas 45°", "Piernas", "4 x 12", 90, "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop&q=80", 2),
            ("Curl Femoral Tumbado", "Isquiosurales", "3 x 12", 60, "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=300&auto=format&fit=crop&q=80", 3),
            ("Elevación de Talones en Máquina", "Gemelos", "4 x 15", 45, "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300&auto=format&fit=crop&q=80", 4),
        ]
        for name, mg, sr, rest, img, ord_num in exercises_miercoles:
            RoutineExercise.objects.create(
                routine_day=day_miercoles,
                name=name,
                muscle_group=mg,
                series_reps=sr,
                rest_seconds=rest,
                image_url=img,
                order=ord_num
            )

        # Ejercicios para el Jueves
        exercises_jueves = [
            ("Press Militar con Barra", "Hombros", "4 x 8", 90, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=300&auto=format&fit=crop&q=80", 1),
            ("Elevaciones Laterales con Mancuernas", "Deltoides Medio", "4 x 15", 45, "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=300&auto=format&fit=crop&q=80", 2),
            ("Pájaros en Polea Posterior", "Deltoides Posterior", "3 x 15", 45, "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop&q=80", 3),
            ("Fondos Tríceps en Banco", "Tríceps", "3 x 15", 45, "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=300&auto=format&fit=crop&q=80", 4),
        ]
        for name, mg, sr, rest, img, ord_num in exercises_jueves:
            RoutineExercise.objects.create(
                routine_day=day_jueves,
                name=name,
                muscle_group=mg,
                series_reps=sr,
                rest_seconds=rest,
                image_url=img,
                order=ord_num
            )

        # Ejercicios para el Viernes
        exercises_viernes = [
            ("Peso Muerto Rumano", "Cadena Posterior", "4 x 10", 90, "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=300&auto=format&fit=crop&q=80", 1),
            ("Dominadas con Agarre Neutro", "Espalda/Brazos", "3 x 10", 90, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=300&auto=format&fit=crop&q=80", 2),
            ("Flexiones con Déficit", "Pecho/Core", "3 x 15", 60, "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop&q=80", 3),
        ]
        for name, mg, sr, rest, img, ord_num in exercises_viernes:
            RoutineExercise.objects.create(
                routine_day=day_viernes,
                name=name,
                muscle_group=mg,
                series_reps=sr,
                rest_seconds=rest,
                image_url=img,
                order=ord_num
            )

        # 6. Mediciones Corporales Históricas
        BodyMetric.objects.filter(member=member_martin).delete()
        metrics_data = [
            (date(2026, 8, 24), Decimal("78.50"), Decimal("18.2"), Decimal("42.10"), Decimal("86.00"), Decimal("102.00")),
            (date(2026, 8, 10), Decimal("79.30"), Decimal("18.6"), Decimal("41.80"), Decimal("87.00"), Decimal("101.50")),
            (date(2026, 7, 27), Decimal("80.20"), Decimal("19.1"), Decimal("41.50"), Decimal("88.50"), Decimal("101.00")),
            (date(2026, 7, 15), Decimal("79.00"), Decimal("18.5"), Decimal("41.70"), Decimal("87.50"), Decimal("101.50")),
            (date(2026, 7, 1), Decimal("79.40"), Decimal("18.8"), Decimal("41.60"), Decimal("88.00"), Decimal("101.00")),
            (date(2026, 6, 15), Decimal("80.10"), Decimal("19.3"), Decimal("41.30"), Decimal("89.00"), Decimal("100.50")),
            (date(2026, 6, 1), Decimal("80.80"), Decimal("19.5"), Decimal("41.20"), Decimal("89.50"), Decimal("100.00")),
        ]
        for dt, w, fat, muscle, waist, chest in metrics_data:
            BodyMetric.objects.create(
                member=member_martin,
                date=dt,
                weight_kg=w,
                body_fat_pct=fat,
                muscle_mass_kg=muscle,
                waist_cm=waist,
                chest_cm=chest
            )

        # 7. Récords Personales (PRs)
        PersonalRecord.objects.filter(member=member_martin).delete()
        prs_data = [
            ("Press de Banca Plano", Decimal("85.00"), date(2026, 8, 12), "fire", 1),
            ("Sentadilla Trasera", Decimal("120.00"), date(2026, 7, 5), "crown", 2),
            ("Peso Muerto Convencional", Decimal("140.00"), date(2026, 6, 20), "bolt", 3),
        ]
        for name, w, dt, badge, ord_num in prs_data:
            PersonalRecord.objects.create(
                member=member_martin,
                exercise_name=name,
                weight_kg=w,
                achieved_date=dt,
                badge_type=badge,
                order=ord_num
            )

        # 8. Actividad Semanal
        MemberActivityDay.objects.filter(member=member_martin).delete()
        activity_data = [
            (date(2026, 8, 17), "Lunes", 17, "ENTRENADO"),
            (date(2026, 8, 18), "Martes", 18, "ENTRENADO"),
            (date(2026, 8, 19), "Miércoles", 19, "DESCANSO"),
            (date(2026, 8, 20), "Jueves", 20, "ENTRENADO"),
            (date(2026, 8, 21), "Viernes", 21, "ENTRENADO"),
            (date(2026, 8, 22), "Sábado", 22, "DESCANSO"),
            (date(2026, 8, 23), "Domingo", 23, "DESCANSO"),
        ]
        for dt, dname, dnum, st in activity_data:
            MemberActivityDay.objects.create(
                member=member_martin,
                date=dt,
                day_name=dname,
                day_number=dnum,
                status=st
            )

        # 9. Clases del Día y Reservas
        cat_crossfit, _ = ClassCategory.objects.get_or_create(name="Crossfit", defaults={"color": "#f5b82e", "description": "WOD de alta intensidad"})
        cat_spinning, _ = ClassCategory.objects.get_or_create(name="Spinning", defaults={"color": "#00f2fe", "description": "Ciclismo indoor"})
        cat_yoga, _ = ClassCategory.objects.get_or_create(name="Yoga", defaults={"color": "#4facfe", "description": "Power Flow & Flexibilidad"})

        today = timezone.now().date()
        # Sesión 1: Spinning 08:00
        sess1, _ = ClassSession.objects.get_or_create(
            category=cat_spinning,
            trainer=trainer_mario,
            date=today,
            start_time="08:00:00",
            defaults={"end_time": "09:00:00", "capacity": 20, "status": "PROGRAMADA", "title": "Spinning Pro"}
        )
        # Booking Spinning: ASISTIO / REALIZADO
        ClassBooking.objects.get_or_create(
            session=sess1,
            member=member_martin,
            defaults={"status": "ASISTIO"}
        )

        # Sesión 2: Crossfit WOD 18:00
        sess2, _ = ClassSession.objects.get_or_create(
            category=cat_crossfit,
            trainer=trainer_lucas,
            date=today,
            start_time="18:00:00",
            defaults={"end_time": "19:15:00", "capacity": 15, "status": "PROGRAMADA", "title": "Crossfit WOD"}
        )
        # Booking Crossfit: RESERVADO
        ClassBooking.objects.get_or_create(
            session=sess2,
            member=member_martin,
            defaults={"status": "RESERVADO"}
        )

        # Sesión 3: Power Yoga 19:30
        sess3, _ = ClassSession.objects.get_or_create(
            category=cat_yoga,
            trainer=trainer_ana,
            date=today,
            start_time="19:30:00",
            defaults={"end_time": "20:30:00", "capacity": 25, "status": "PROGRAMADA", "title": "Power Yoga Flow"}
        )

        self.stdout.write(self.style.SUCCESS("[OK] Datos de prueba para el Portal de Socios sembrados con éxito."))

