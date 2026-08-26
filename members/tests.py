from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Plan, Member


class MemberTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin_test',
            password='TestPassword123!',
            email='members@vitalis.com'
        )
        
        self.plan_vip = Plan.objects.create(
            name="Black Pass VIP",
            price=65000,
            duration_days=30,
            color="#f5b82e"
        )
        
        self.member = Member.objects.create(
            first_name="Sofía",
            last_name="Rodriguez",
            dni="18.432.910-K",
            email="sofia@email.com",
            phone="+56987654321",
            plan=self.plan_vip,
            status="ACTIVA"
        )

    def test_member_creation_and_end_date_auto_calc(self):
        """Verifica que el socio se cree y su fecha de fin se calcule automáticamente."""
        self.assertEqual(self.member.full_name, "Sofía Rodriguez")
        self.assertIsNotNone(self.member.end_date)
        self.assertEqual(self.member.status_badge_class, "badge-success")

    def test_member_list_unauthenticated_redirect(self):
        """Un usuario anónimo debe ser redirigido al login."""
        response = self.client.get(reverse('members:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response.url)

    def test_member_list_authenticated_access(self):
        """Un usuario autenticado puede ver el listado de socios."""
        self.client.login(username='admin_test', password='TestPassword123!')
        response = self.client.get(reverse('members:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/member_list.html')
        self.assertContains(response, "Sofía Rodriguez")
        self.assertContains(response, "18.432.910-K")

    def test_member_search_filter(self):
        """Verifica que la búsqueda por DNI y nombre filtre correctamente."""
        self.client.login(username='admin_test', password='TestPassword123!')
        response = self.client.get(reverse('members:list') + '?q=18.432')
        self.assertContains(response, "Sofía Rodriguez")

        response_empty = self.client.get(reverse('members:list') + '?q=Inexistente999')
        self.assertNotContains(response_empty, "18.432.910-K")

    def test_member_detail_view(self):
        """Verifica la vista de ficha técnica del socio."""
        self.client.login(username='admin_test', password='TestPassword123!')
        response = self.client.get(reverse('members:detail', args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/member_detail.html')
        self.assertContains(response, "Black Pass VIP")
        self.assertContains(response, "Acceso a la App de Clientes")

    def test_member_create_auto_user_and_routine(self):
        """Verifica que al crear un socio se genere su cuenta de usuario y rutina base."""
        self.client.login(username='admin_test', password='TestPassword123!')
        url = reverse('members:create')
        response = self.client.post(url, {
            'first_name': 'Esteban',
            'last_name': 'Morales',
            'dni': '20111222',
            'email': 'esteban@ejemplo.com',
            'phone': '+56911223344',
            'gender': 'M',
            'plan': self.plan_vip.pk,
            'status': 'ACTIVA',
            'start_date': '2026-08-25',
        })
        self.assertEqual(response.status_code, 302)
        new_member = Member.objects.get(dni='20111222')
        self.assertIsNotNone(new_member.user)
        self.assertEqual(new_member.user.username, '20111222')
        # Verificar que la rutina base se haya asignado
        self.assertTrue(new_member.routines.filter(is_active=True).exists())

    def test_member_reset_portal_password(self):
        """Verifica el reseteo de clave del portal para el socio."""
        self.client.login(username='admin_test', password='TestPassword123!')
        url = reverse('members:reset_portal_password', args=[self.member.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertIsNotNone(self.member.user)
        # Autenticar con el DNI limpio como password
        clean_dni = self.member.dni.strip().replace('.', '').replace('-', '')
        self.assertTrue(self.client.login(username=clean_dni, password=clean_dni))

    def test_kiosk_terminal_view_renders(self):
        """Verifica que la pantalla del terminal kiosko renderice correctamente."""
        response = self.client.get(reverse('members:terminal'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/kiosk_terminal.html')
        self.assertContains(response, 'REGISTRO DE INGRESO')
        self.assertContains(response, 'Tótem de Acceso Activo')

    def test_kiosk_checkin_success_active_member(self):
        """Verifica que un socio activo al día reciba confirmación verde y se registre su check-in."""
        from members.models import MemberCheckIn
        url = reverse('members:terminal_checkin')
        response = self.client.post(url, {'dni': '18.432.910-K'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Sofía', data['title'])
        self.assertEqual(data['member_name'], 'Sofía Rodriguez')
        self.assertTrue(MemberCheckIn.objects.filter(member=self.member, status='PERMITIDO').exists())

    def test_kiosk_checkin_expired_member(self):
        """Verifica que un socio con membresía vencida reciba alerta roja."""
        from datetime import date, timedelta
        from members.models import MemberCheckIn
        self.member.end_date = date.today() - timedelta(days=5)
        self.member.status = 'VENCIDO'
        self.member.save()

        url = reverse('members:terminal_checkin')
        response = self.client.post(url, {'dni': self.member.dni})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'expired')
        self.assertEqual(data['title'], 'Membresía Vencida')
        self.assertTrue(MemberCheckIn.objects.filter(member=self.member, status='VENCIDO').exists())

    def test_kiosk_checkin_not_found(self):
        """Verifica el comportamiento cuando el DNI no existe en el sistema."""
        url = reverse('members:terminal_checkin')
        response = self.client.post(url, {'dni': '9999999999'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'not_found')
        self.assertEqual(data['title'], 'DNI No Registrado')

    def test_kiosk_checkin_empty_dni(self):
        """Verifica que un DNI vacío devuelva error 400."""
        url = reverse('members:terminal_checkin')
        response = self.client.post(url, {'dni': ''})
        self.assertEqual(response.status_code, 400)

    def test_checkin_list_view_authenticated(self):
        """Verifica que el staff pueda ver el feed en vivo de accesos."""
        from members.models import MemberCheckIn
        MemberCheckIn.objects.create(member=self.member, status='PERMITIDO')
        self.client.login(username='admin_test', password='TestPassword123!')
        response = self.client.get(reverse('members:checkin_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'members/checkin_list.html')
        self.assertContains(response, 'Control de Accesos en Vivo')
        self.assertContains(response, self.member.full_name)
