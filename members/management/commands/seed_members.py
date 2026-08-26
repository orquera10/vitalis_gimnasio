from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from members.models import Plan, Member


class Command(BaseCommand):
    help = "Puebla la base de datos con planes y socios iniciales de Vitalis Fitness"

    def handle(self, *args, **options):
        self.stdout.write("Creando planes de membresía...")

        # 1. Crear Planes
        plan_vip, _ = Plan.objects.get_or_create(
            name="Black Pass VIP",
            defaults={
                'price': 65000.00,
                'duration_days': 30,
                'color': '#f5b82e',
                'description': 'Acceso ilimitado a todas las sedes, clases premium, sauna y evaluación física mensual.',
                'is_active': True,
            }
        )

        plan_studio, _ = Plan.objects.get_or_create(
            name="Membresía Studio",
            defaults={
                'price': 42000.00,
                'duration_days': 30,
                'color': '#e2e8f0',
                'description': 'Acceso a sala de musculación, cardio y 8 clases grupales por mes.',
                'is_active': True,
            }
        )

        plan_standard, _ = Plan.objects.get_or_create(
            name="Pase Estándar",
            defaults={
                'price': 29900.00,
                'duration_days': 30,
                'color': '#64748b',
                'description': 'Acceso en horario valle (09:00 a 16:00) a sala de musculación.',
                'is_active': True,
            }
        )

        self.stdout.write("Creando socios de muestra (diseño Figma + adicionales)...")

        members_data = [
            {
                'first_name': 'Sofía',
                'last_name': 'Rodriguez',
                'dni': '18.432.910-K',
                'email': 'sofia.rodriguez@email.com',
                'phone': '+56 9 8765 4321',
                'gender': 'F',
                'date_of_birth': date(1996, 5, 14),
                'avatar': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
                'plan': plan_vip,
                'status': 'ACTIVA',
                'start_date': date(2026, 1, 15),
                'end_date': date(2026, 9, 15),
                'emergency_contact_name': 'Mariana Rodriguez (Madre)',
                'emergency_contact_phone': '+56 9 1122 3344',
                'medical_notes': 'Apta para alta intensidad. Sin alergias.',
            },
            {
                'first_name': 'Carlos',
                'last_name': 'Mendoza',
                'dni': '17.890.123-4',
                'email': 'carlos.mendoza@email.com',
                'phone': '+56 9 7654 3210',
                'gender': 'M',
                'date_of_birth': date(1992, 8, 22),
                'avatar': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80',
                'plan': plan_studio,
                'status': 'PENDIENTE',
                'start_date': date(2026, 2, 2),
                'end_date': date(2026, 8, 2),
                'emergency_contact_name': 'Lucía Mendoza (Hermana)',
                'emergency_contact_phone': '+56 9 9988 7766',
                'medical_notes': 'Comprobante de transferencia bancaria en revisión.',
            },
            {
                'first_name': 'Valentina',
                'last_name': 'Ortiz',
                'dni': '19.554.321-7',
                'email': 'valentina.ortiz@email.com',
                'phone': '+56 9 6543 2109',
                'gender': 'F',
                'date_of_birth': date(1998, 11, 30),
                'avatar': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&auto=format&fit=crop&q=80',
                'plan': plan_standard,
                'status': 'VENCIDO',
                'start_date': date(2025, 11, 12),
                'end_date': date(2025, 12, 12),
                'emergency_contact_name': 'Esteban Ortiz (Padre)',
                'emergency_contact_phone': '+56 9 3344 5566',
                'medical_notes': 'Membresía vencida. Notificada por correo.',
            },
            {
                'first_name': 'Mateo',
                'last_name': 'Silva',
                'dni': '16.789.012-3',
                'email': 'mateo.silva@email.com',
                'phone': '+56 9 5432 1098',
                'gender': 'M',
                'date_of_birth': date(1990, 3, 18),
                'avatar': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80',
                'plan': plan_vip,
                'status': 'ACTIVA',
                'start_date': date(2026, 1, 28),
                'end_date': date(2026, 10, 28),
                'emergency_contact_name': 'Camila Silva (Esposa)',
                'emergency_contact_phone': '+56 9 7788 9900',
                'medical_notes': 'Molestia leve en manguito rotador derecho.',
            },
            {
                'first_name': 'Ignacio',
                'last_name': 'Valenzuela',
                'dni': '15.987.654-2',
                'email': 'ignacio.valenzuela@email.com',
                'phone': '+56 9 4321 0987',
                'gender': 'M',
                'date_of_birth': date(1988, 7, 9),
                'avatar': 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=120&auto=format&fit=crop&q=80',
                'plan': plan_vip,
                'status': 'ACTIVA',
                'start_date': date(2026, 2, 10),
                'end_date': date(2026, 11, 10),
                'emergency_contact_name': 'Daniela Valenzuela',
                'emergency_contact_phone': '+56 9 2233 4455',
                'medical_notes': 'Apto sin restricciones.',
            },
            {
                'first_name': 'Florencia',
                'last_name': 'Navarro',
                'dni': '20.123.456-1',
                'email': 'florencia.navarro@email.com',
                'phone': '+56 9 3210 9876',
                'gender': 'F',
                'date_of_birth': date(2001, 12, 5),
                'avatar': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80',
                'plan': plan_studio,
                'status': 'ACTIVA',
                'start_date': date(2026, 3, 1),
                'end_date': date(2026, 9, 1),
                'emergency_contact_name': 'Rodrigo Navarro',
                'emergency_contact_phone': '+56 9 6655 4433',
                'medical_notes': 'Entrenamiento orientado a hipertrofia.',
            }
        ]

        for m_data in members_data:
            Member.objects.update_or_create(
                dni=m_data['dni'],
                defaults=m_data
            )

        self.stdout.write(self.style.SUCCESS(f"¡Se han creado {len(members_data)} socios y 3 planes exitosamente!"))
