from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from core.models import GymSetting
from members.models import Plan
from classes.models import ClassCategory


class CoreAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'gymadmin'
        self.password = 'StrongGymPassword123!'
        self.user = User.objects.create_superuser(
            username=self.username,
            password=self.password,
            email='admin@vitalis.com',
            first_name='Admin'
        )

    def test_login_page_renders_correctly(self):
        """Verifica que la página de login responda con status 200 y use el template adecuado."""
        response = self.client.get(reverse('core:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/login.html')
        self.assertContains(response, 'VITALIS')

    def test_unauthenticated_user_redirected_from_home(self):
        """Un usuario no autenticado debe ser redirigido al login al intentar acceder a la vista home."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response.url)

    def test_authenticated_user_can_access_home(self):
        """Un usuario autenticado puede acceder a la vista home y ver el dashboard."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertContains(response, 'Total Miembros')
        self.assertContains(response, 'Tendencia de Ingresos')

    def test_logout_view(self):
        """Verifica que cerrar sesión funcione y redirija al login."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('core:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:login'))

    def test_settings_view_authenticated(self):
        """Acceso al centro de configuración y renderizado de pestañas."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('core:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/settings.html')
        self.assertContains(response, 'Centro de Configuración & Ajustes')
        self.assertContains(response, 'Vitalis Fitness Club')

    def test_settings_update_post(self):
        """Actualización de datos del gimnasio."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('core:settings'), {
            'gym_name': 'Vitalis Elite Club',
            'branch_name': 'Sede Belgrano',
            'tax_id': '30-99887766-5',
            'address': 'Av. Cabildo 2000',
            'phone': '+54 11 4444-5555',
            'whatsapp': '+54 9 11 3333-2222',
            'email': 'belgrano@vitalis.com',
            'bank_cbu': '1234567890123456789012',
            'bank_alias': 'VITALIS.BELGRANO',
            'receipt_footer': 'Comprobante válido.',
            'days_advance_notice': 10,
            'grace_period_days': 5,
            'default_class_capacity': 20,
            'active_tab': 'tab-general'
        })
        self.assertEqual(response.status_code, 200)
        setting = GymSetting.get_settings()
        self.assertEqual(setting.gym_name, 'Vitalis Elite Club')
        self.assertEqual(setting.branch_name, 'Sede Belgrano')

    def test_plan_create_and_delete(self):
        """Creación y eliminación de planes desde configuración."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('core:plan_create'), {
            'name': 'Pase Fin de Semana VIP',
            'price': Decimal('35000.00'),
            'duration_days': 30,
            'color': '#f5b82e',
            'description': 'Solo Sábados y Domingos',
            'is_active': True
        })
        self.assertEqual(response.status_code, 302)
        plan = Plan.objects.get(name='Pase Fin de Semana VIP')
        self.assertEqual(plan.price, Decimal('35000.00'))

        # Eliminar plan
        del_response = self.client.post(reverse('core:plan_delete', kwargs={'pk': plan.pk}))
        self.assertEqual(del_response.status_code, 302)
        self.assertFalse(Plan.objects.filter(name='Pase Fin de Semana VIP').exists())

    def test_backup_json_download(self):
        """Descarga de archivo de copia de seguridad JSON."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('core:backup'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertIn('attachment; filename="vitalis_backup_', response['Content-Disposition'])

    def test_user_create_modal_receptionist(self):
        """Creación de un usuario empleado con rol de recepcionista."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('core:user_create'), {
            'first_name': 'Lucía',
            'last_name': 'Gómez',
            'username': 'lucia.recepcion',
            'email': 'lucia@vitalis.com',
            'password': 'Password123!',
            'role': 'receptionist',
            'is_active': 'on'
        })
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='lucia.recepcion')
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(name='Recepcionistas').exists())

    def test_user_toggle_status_and_delete(self):
        """Activar/Desactivar y eliminar empleados con protección contra auto-modificación."""
        self.client.login(username=self.username, password=self.password)
        emp = User.objects.create_user(
            username='carlos.profe',
            password='Password123!',
            first_name='Carlos',
            is_active=True
        )

        # Toggle status
        toggle_resp = self.client.post(reverse('core:user_toggle', kwargs={'pk': emp.pk}))
        self.assertEqual(toggle_resp.status_code, 200)
        emp.refresh_from_db()
        self.assertFalse(emp.is_active)

        # Protección: No se puede desactivar a sí mismo
        self_toggle = self.client.post(reverse('core:user_toggle', kwargs={'pk': self.user.pk}))
        self.assertEqual(self_toggle.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Eliminar usuario
        del_resp = self.client.post(reverse('core:user_delete', kwargs={'pk': emp.pk}))
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='carlos.profe').exists())

    def test_trainer_blocked_from_restricted_modules(self):
        """Un usuario profesor/entrenador no puede entrar a reportes, pagos, configuración ni crear socios."""
        from core.views_settings import get_or_create_staff_groups
        _, _, trainer_group = get_or_create_staff_groups()
        
        trainer_user = User.objects.create_user(
            username='marcos.entrenador',
            password='TrainerPass123!',
            first_name='Marcos'
        )
        trainer_user.groups.add(trainer_group)

        self.client.login(username='marcos.entrenador', password='TrainerPass123!')

        # 1. Puede acceder al Dashboard y al Almanaque de Clases
        self.assertEqual(self.client.get(reverse('core:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('classes:calendar')).status_code, 200)

        # 2. BLOQUEADO de Reportes (Redirige a home con mensaje de error)
        resp_rep = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(resp_rep.status_code, 302)
        self.assertEqual(resp_rep.url, reverse('core:home'))

        # 3. BLOQUEADO de Pagos (Redirige a home)
        resp_pay = self.client.get(reverse('payments:list'))
        self.assertEqual(resp_pay.status_code, 302)
        self.assertEqual(resp_pay.url, reverse('core:home'))

        # 4. BLOQUEADO de Configuración (Redirige a home)
        resp_set = self.client.get(reverse('core:settings'))
        self.assertEqual(resp_set.status_code, 302)
        self.assertEqual(resp_set.url, reverse('core:home'))

        # 5. BLOQUEADO de Crear Socios
        resp_mem_create = self.client.get(reverse('members:create'))
        self.assertEqual(resp_mem_create.status_code, 302)
        self.assertEqual(resp_mem_create.url, reverse('members:list'))

    def test_receptionist_permissions(self):
        """Un usuario recepcionista puede entrar a pagos y socios, pero no a reportes ni configuración."""
        from core.views_settings import get_or_create_staff_groups
        _, recep_group, _ = get_or_create_staff_groups()
        
        recep_user = User.objects.create_user(
            username='ana.recepcion',
            password='RecepPass123!',
            first_name='Ana'
        )
        recep_user.groups.add(recep_group)

        self.client.login(username='ana.recepcion', password='RecepPass123!')

        # 1. Puede acceder a Pagos y a Socios
        self.assertEqual(self.client.get(reverse('payments:list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('members:create')).status_code, 200)

        # 2. BLOQUEADO de Reportes
        resp_rep = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(resp_rep.status_code, 302)
        self.assertEqual(resp_rep.url, reverse('core:home'))

        # 3. BLOQUEADO de Configuración
        resp_set = self.client.get(reverse('core:settings'))
        self.assertEqual(resp_set.status_code, 302)
        self.assertEqual(resp_set.url, reverse('core:home'))
