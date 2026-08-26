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
