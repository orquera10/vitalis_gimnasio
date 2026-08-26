from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time, timedelta
from classes.models import Trainer, ClassCategory, ClassSchedule, ClassSession


class Command(BaseCommand):
    help = "Puebla la base de datos con entrenadores, disciplinas y clases (incluyendo Funcional Miércoles y Viernes de 20:00 a 22:00)"

    def handle(self, *args, **options):
        self.stdout.write("Creando entrenadores...")

        trainers_data = [
            {
                'first_name': 'Lucas',
                'last_name': 'Torres',
                'specialty': 'Funcional & Crossfit Coach',
                'email': 'lucas.torres@vitalisfitness.com',
                'phone': '+56 9 9123 4567',
                'avatar': 'https://images.unsplash.com/photo-1568602471122-7832951cc4c5?w=120&auto=format&fit=crop&q=80',
                'bio': 'Especialista en acondicionamiento físico, entrenamiento funcional de alta intensidad y cross training con 8 años de experiencia.'
            },
            {
                'first_name': 'Ana',
                'last_name': 'Sofía',
                'specialty': 'Power Yoga & Flexibilidad',
                'email': 'ana.sofia@vitalisfitness.com',
                'phone': '+56 9 8234 5678',
                'avatar': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80',
                'bio': 'Instructora certificada de Vinyasa y Ashtanga Yoga. Especialista en movilidad articular y reducción del estrés.'
            },
            {
                'first_name': 'Mario',
                'last_name': 'Ruiz',
                'specialty': 'Indoor Cycling & HIIT',
                'email': 'mario.ruiz@vitalisfitness.com',
                'phone': '+56 9 7345 6789',
                'avatar': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80',
                'bio': 'Entrenador de alta exigencia cardiovascular, spinning y resistencia metabólica.'
            }
        ]

        trainers = {}
        for t_data in trainers_data:
            tr, _ = Trainer.objects.update_or_create(
                email=t_data['email'],
                defaults=t_data
            )
            trainers[tr.first_name] = tr

        self.stdout.write("Creando disciplinas...")

        categories_data = [
            {'name': 'Entrenamiento Funcional', 'color': '#f5b82e', 'description': 'Ejercicios multiarticulares para fuerza, agilidad y resistencia metabólica.'},
            {'name': 'Crossfit WOD', 'color': '#06b6d4', 'description': 'Workout of the Day con levantamiento olímpico y gimnasia.'},
            {'name': 'Power Yoga Flow', 'color': '#84cc16', 'description': 'Secuencias dinámicas de posturas con respiración consciente.'},
            {'name': 'Spinning Pro', 'color': '#f59e0b', 'description': 'Ciclismo indoor de alta intensidad por intervalos.'},
            {'name': 'HIIT Training', 'color': '#ec4899', 'description': 'Intervalos cortos de esfuerzo máximo para quema calórica.'},
        ]

        categories = {}
        for cat_data in categories_data:
            c, _ = ClassCategory.objects.update_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[c.name] = c

        self.stdout.write("Creando horarios recurrentes (ej. Funcional Miércoles y Viernes de 20:00 a 22:00)...")

        schedules_data = [
            # 1. ENTRENAMIENTO FUNCIONAL: MIÉRCOLES (3) y VIERNES (5) de 20:00 a 22:00
            {
                'title': 'Entrenamiento Funcional Nocturno',
                'category': categories['Entrenamiento Funcional'],
                'trainer': trainers['Lucas'],
                'days': [3, 5], # Miércoles y Viernes
                'start_time': time(20, 0),
                'end_time': time(22, 0),
                'room': 'Box Funcional Principal',
                'capacity': 20
            },
            # 2. Crossfit WOD: Lunes a Viernes 08:00 a 09:30
            {
                'title': 'Crossfit WOD Matutino',
                'category': categories['Crossfit WOD'],
                'trainer': trainers['Lucas'],
                'days': [1, 2, 3, 4, 5],
                'start_time': time(8, 0),
                'end_time': time(9, 30),
                'room': 'Box Central',
                'capacity': 15
            },
            # 3. Power Yoga Flow: Martes y Jueves 09:30 a 11:00
            {
                'title': 'Power Yoga Flow',
                'category': categories['Power Yoga Flow'],
                'trainer': trainers['Ana'],
                'days': [2, 4],
                'start_time': time(9, 30),
                'end_time': time(11, 0),
                'room': 'Studio Zen',
                'capacity': 18
            },
            # 4. Spinning Pro: Lunes, Miércoles, Viernes 11:00 a 12:30
            {
                'title': 'Spinning Pro Interval',
                'category': categories['Spinning Pro'],
                'trainer': trainers['Mario'],
                'days': [1, 3, 5],
                'start_time': time(11, 0),
                'end_time': time(12, 30),
                'room': 'Sala Spinning',
                'capacity': 25
            },
            # 5. HIIT Training: Lunes a Jueves 18:30 a 19:45
            {
                'title': 'HIIT Training Quema-Grasa',
                'category': categories['HIIT Training'],
                'trainer': trainers['Lucas'],
                'days': [1, 2, 3, 4],
                'start_time': time(18, 30),
                'end_time': time(19, 45),
                'room': 'Sala Funcional 2',
                'capacity': 16
            },
        ]

        today = timezone.now().date()
        # Inicio de la semana actual (Lunes)
        monday = today - timedelta(days=today.weekday())

        for sch_info in schedules_data:
            for day_num in sch_info['days']:
                sch, _ = ClassSchedule.objects.update_or_create(
                    title=sch_info['title'],
                    day_of_week=day_num,
                    start_time=sch_info['start_time'],
                    defaults={
                        'category': sch_info['category'],
                        'trainer': sch_info['trainer'],
                        'end_time': sch_info['end_time'],
                        'room': sch_info['room'],
                        'capacity': sch_info['capacity'],
                        'is_active': True,
                    }
                )

                # Generar sesiones para las semanas previa, actual y próximas 3 semanas
                for week_offset in range(-1, 4):
                    session_date = monday + timedelta(days=(day_num - 1) + (week_offset * 7))
                    
                    # Simular cupos reservados
                    booked = 16 if sch_info['title'].startswith('Crossfit') else (8 if sch_info['title'].startswith('Entrenamiento') else 10)
                    if session_date == today and sch_info['start_time'] == time(11, 0):
                        booked = sch_info['capacity'] # Simular agotado para Spinning hoy

                    sess, _ = ClassSession.objects.get_or_create(
                        schedule=sch,
                        date=session_date,
                        start_time=sch_info['start_time'],
                        defaults={
                            'title': sch_info['title'],
                            'category': sch_info['category'],
                            'trainer': sch_info['trainer'],
                            'end_time': sch_info['end_time'],
                            'room': sch_info['room'],
                            'capacity': sch_info['capacity'],
                            'booked_count': 0,
                            'status': 'PROGRAMADA'
                        }
                    )

        # Inscribir algunos socios de ejemplo
        from members.models import Member
        from classes.models import ClassBooking
        active_members = list(Member.objects.filter(status='ACTIVA')[:6])
        recent_sessions = ClassSession.objects.filter(date__gte=today)[:3]

        if active_members and recent_sessions:
            for s in recent_sessions:
                for idx, m in enumerate(active_members[:3]):
                    status = 'PRESENTE' if idx == 0 else 'RESERVADO'
                    ClassBooking.objects.get_or_create(
                        session=s,
                        member=m,
                        defaults={
                            'status': status,
                            'notes': 'Inscripción regular' if idx > 0 else 'Asistencia confirmada'
                        }
                    )

        self.stdout.write(self.style.SUCCESS("¡Se han generado los entrenadores, disciplinas, horarios recurrentes, sesiones de almanaque e inscripciones exitosamente!"))
