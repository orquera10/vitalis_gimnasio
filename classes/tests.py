from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, date
from members.models import Member, Plan
from .models import Trainer, ClassCategory, ClassSchedule, ClassSession, ClassBooking


class ClassTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin_classes',
            password='TestPassword123!',
            email='classes@vitalis.com'
        )
        
        self.trainer = Trainer.objects.create(
            first_name="Lucas",
            last_name="Torres",
            specialty="Funcional & Crossfit",
            email="lucas@vitalis.com"
        )
        
        self.category = ClassCategory.objects.create(
            name="Entrenamiento Funcional",
            color="#f5b82e"
        )
        
        self.schedule_wed = ClassSchedule.objects.create(
            title="Entrenamiento Funcional",
            category=self.category,
            trainer=self.trainer,
            day_of_week=3, # Miércoles
            start_time=time(20, 0),
            end_time=time(22, 0),
            room="Box Funcional",
            capacity=20
        )
        
        self.schedule_fri = ClassSchedule.objects.create(
            title="Entrenamiento Funcional",
            category=self.category,
            trainer=self.trainer,
            day_of_week=5, # Viernes
            start_time=time(20, 0),
            end_time=time(22, 0),
            room="Box Funcional",
            capacity=20
        )
        
        self.session = ClassSession.objects.create(
            schedule=self.schedule_wed,
            title="Entrenamiento Funcional",
            category=self.category,
            trainer=self.trainer,
            date=timezone.now().date(),
            start_time=time(20, 0),
            end_time=time(22, 0),
            room="Box Funcional",
            capacity=20,
            booked_count=0
        )

        self.plan = Plan.objects.create(
            name="Pase Libre",
            price=25000,
            duration_days=30
        )

        self.active_member = Member.objects.create(
            first_name="Martín",
            last_name="Gómez",
            dni="38123456",
            email="martin@ejemplo.com",
            plan=self.plan,
            status='ACTIVA'
        )

        self.inactive_member = Member.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            dni="39123456",
            email="carlos@ejemplo.com",
            plan=self.plan,
            status='INACTIVA'
        )

    def test_class_session_properties(self):
        """Verifica el cálculo de cupos disponibles y rangos de tiempo."""
        self.assertEqual(self.session.available_spots, 20)
        self.assertFalse(self.session.is_full)
        self.assertEqual(self.session.time_range, "20:00 - 22:00")

    def test_calendar_view_unauthenticated(self):
        """Usuario anónimo es redirigido al login."""
        response = self.client.get(reverse('classes:calendar'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response.url)

    def test_calendar_view_authenticated(self):
        """Usuario autenticado puede acceder al almanaque y ver las clases semanales."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        response = self.client.get(reverse('classes:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'classes/calendar.html')
        self.assertContains(response, "Almanaque de Clases")
        self.assertContains(response, "Entrenamiento Funcional")

    def test_class_detail_view(self):
        """Verifica la vista de detalle de una sesión."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        response = self.client.get(reverse('classes:detail', args=[self.session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'classes/class_detail.html')
        self.assertContains(response, "Box Funcional")
        self.assertContains(response, "Lucas Torres")

    def test_member_enrollment_success(self):
        """Inscribir un socio activo descuenta 1 cupo y crea la reserva."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:booking_create', args=[self.session.pk])
        response = self.client.post(url, {
            'member': self.active_member.pk,
            'notes': 'Primera clase de prueba'
        })
        self.assertEqual(response.status_code, 302)
        
        self.session.refresh_from_db()
        self.assertEqual(self.session.booked_count, 1)
        self.assertEqual(self.session.available_spots, 19)
        self.assertTrue(ClassBooking.objects.filter(session=self.session, member=self.active_member).exists())

    def test_member_enrollment_inactive_membership_rejected(self):
        """Un socio con membresía inactiva no puede ser inscripto a la clase."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:booking_create', args=[self.session.pk])
        response = self.client.post(url, {
            'member': self.inactive_member.pk,
        })
        self.assertEqual(response.status_code, 302)
        
        self.session.refresh_from_db()
        self.assertEqual(self.session.booked_count, 0)
        self.assertFalse(ClassBooking.objects.filter(session=self.session, member=self.inactive_member).exists())

    def test_member_enrollment_duplicate_rejected(self):
        """Un socio no puede ser inscripto dos veces a la misma sesión."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:booking_create', args=[self.session.pk])
        # Primera inscripción
        self.client.post(url, {'member': self.active_member.pk})
        # Segunda inscripción idéntica
        self.client.post(url, {'member': self.active_member.pk})
        
        self.session.refresh_from_db()
        self.assertEqual(self.session.booked_count, 1)
        self.assertEqual(ClassBooking.objects.filter(session=self.session, member=self.active_member).count(), 1)

    def test_member_enrollment_full_capacity_rejected(self):
        """Si la clase está llena, no se permiten nuevas inscripciones."""
        self.session.capacity = 1
        self.session.save()
        
        ClassBooking.objects.create(session=self.session, member=self.active_member)
        self.session.refresh_from_db()
        self.assertTrue(self.session.is_full)

        # Crear segundo socio activo
        member2 = Member.objects.create(
            first_name="Laura",
            last_name="Ríos",
            dni="40123456",
            email="laura@ejemplo.com",
            plan=self.plan,
            status='ACTIVA'
        )

        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:booking_create', args=[self.session.pk])
        self.client.post(url, {'member': member2.pk})

        self.assertFalse(ClassBooking.objects.filter(session=self.session, member=member2).exists())

    def test_booking_status_update_and_cancellation(self):
        """Verifica actualización de asistencia (Presente) y cancelación/liberación de cupo."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        booking = ClassBooking.objects.create(session=self.session, member=self.active_member, status='RESERVADO')
        self.session.refresh_from_db()
        self.assertEqual(self.session.booked_count, 1)

        # Marcar Presente
        status_url = reverse('classes:booking_status_update', args=[booking.pk])
        self.client.post(status_url, {'status': 'PRESENTE'})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'PRESENTE')

        # Cancelar reserva
        delete_url = reverse('classes:booking_delete', args=[booking.pk])
        self.client.post(delete_url)
        self.assertFalse(ClassBooking.objects.filter(pk=booking.pk).exists())
        self.session.refresh_from_db()
        self.assertEqual(self.session.booked_count, 0)

    def test_trainer_list_view(self):
        """Usuario autenticado puede listar los entrenadores."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        response = self.client.get(reverse('classes:trainer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'classes/trainer_list.html')
        self.assertContains(response, "Lucas Torres")
        self.assertContains(response, "Directorio de Entrenadores")

    def test_trainer_create_view(self):
        """Se puede registrar un nuevo entrenador mediante el formulario."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:trainer_create')
        response = self.client.post(url, {
            'first_name': 'Valeria',
            'last_name': 'Mendoza',
            'specialty': 'Pilates & Movilidad',
            'email': 'valeria@vitalisfitness.com',
            'phone': '+56 9 8888 7777',
            'bio': 'Certificada en Pilates Reformer.',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Trainer.objects.filter(first_name='Valeria', last_name='Mendoza').exists())

    def test_trainer_detail_view(self):
        """Verifica la vista de detalle y agenda del entrenador."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        response = self.client.get(reverse('classes:trainer_detail', args=[self.trainer.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'classes/trainer_detail.html')
        self.assertContains(response, "Lucas Torres")
        self.assertContains(response, "Horarios Semanales Fijos a Cargo")

    def test_trainer_update_view(self):
        """Se pueden editar los datos de un entrenador existente."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:trainer_update', args=[self.trainer.pk])
        response = self.client.post(url, {
            'first_name': 'Lucas Gabriel',
            'last_name': 'Torres',
            'specialty': 'Funcional, Crossfit & Calistenia',
            'email': 'lucas.torres@vitalis.com',
            'phone': '+56 9 9999 0000',
            'bio': 'Coach senior con nuevas certificaciones.',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.trainer.refresh_from_db()
        self.assertEqual(self.trainer.first_name, 'Lucas Gabriel')
        self.assertEqual(self.trainer.specialty, 'Funcional, Crossfit & Calistenia')

    def test_trainer_delete_view(self):
        """Se puede eliminar un entrenador del directorio."""
        self.client.login(username='admin_classes', password='TestPassword123!')
        url = reverse('classes:trainer_delete', args=[self.trainer.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Trainer.objects.filter(pk=self.trainer.pk).exists())

    def test_trainer_create_with_image_upload(self):
        """Verifica que se pueda registrar un entrenador subiendo un archivo de imagen."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.login(username='admin_classes', password='TestPassword123!')
        
        tiny_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        )
        avatar_file = SimpleUploadedFile('coach_avatar.gif', tiny_gif, content_type='image/gif')

        url = reverse('classes:trainer_create')
        response = self.client.post(url, {
            'first_name': 'Diego',
            'last_name': 'Navarro',
            'specialty': 'Boxeo & Acondicionamiento',
            'email': 'diego@vitalisfitness.com',
            'phone': '+56 9 1234 9999',
            'avatar_file': avatar_file,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        new_trainer = Trainer.objects.get(email='diego@vitalisfitness.com')
        self.assertTrue(bool(new_trainer.avatar_file))
        self.assertIn('coach_avatar', new_trainer.avatar_url)

