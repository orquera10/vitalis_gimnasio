import json
from django.contrib import messages
from .permissions import AdminRequiredMixin
from django.views.generic import View, TemplateView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User, Group, Permission
from .models import GymSetting
from .forms import GymSettingForm, PlanModalForm, CategoryModalForm
from members.models import Plan, Member
from classes.models import ClassCategory, Trainer, ClassSession, ClassBooking
from payments.models import Payment


def get_or_create_staff_groups():
    """
    Crea o recupera los 3 grupos predefinidos para empleados del gimnasio con sus permisos:
    1. Administradores
    2. Recepcionistas (Gestión de socios, cobros, reservas, asistencias)
    3. Entrenadores (Visualización de clases, marcación de asistencias)
    """
    admin_group, _ = Group.objects.get_or_create(name='Administradores')
    recep_group, _ = Group.objects.get_or_create(name='Recepcionistas')
    trainer_group, _ = Group.objects.get_or_create(name='Entrenadores')

    # Permisos para Recepcionistas
    recep_codenames = [
        'add_member', 'change_member', 'view_member',
        'add_payment', 'change_payment', 'view_payment',
        'view_classsession', 'add_classbooking', 'change_classbooking', 'view_classbooking',
        'add_attendance', 'change_attendance', 'view_attendance',
        'view_trainer'
    ]
    recep_perms = Permission.objects.filter(codename__in=recep_codenames)
    recep_group.permissions.set(recep_perms)

    # Permisos para Entrenadores
    trainer_codenames = [
        'view_classsession', 'add_attendance', 'change_attendance', 'view_attendance',
        'view_trainer', 'view_member'
    ]
    trainer_perms = Permission.objects.filter(codename__in=trainer_codenames)
    trainer_group.permissions.set(trainer_perms)

    return admin_group, recep_group, trainer_group


class SettingsView(AdminRequiredMixin, TemplateView):
    """
    Centro ejecutivo de Configuración & Ajustes de Vitalis Fitness.
    """
    template_name = 'core/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_obj = GymSetting.get_settings()
        context['settings_obj'] = settings_obj
        context['form'] = GymSettingForm(instance=settings_obj)
        context['plans'] = Plan.objects.all().order_by('-price')
        context['categories'] = ClassCategory.objects.all().order_by('name')
        context['plan_form'] = PlanModalForm()
        context['category_form'] = CategoryModalForm()
        context['active_tab'] = self.request.GET.get('tab', 'tab-general')

        # 5. Usuarios & Personal del Gimnasio
        get_or_create_staff_groups()
        users_list = []
        for u in User.objects.all().order_by('-is_superuser', '-is_staff', 'username'):
            # Detect role
            if u.is_superuser:
                role_name = 'Administrador'
                role_badge_class = 'badge-gold'
                role_icon = '👑'
            elif u.groups.filter(name='Recepcionistas').exists():
                role_name = 'Recepcionista'
                role_badge_class = 'badge-success'
                role_icon = '🟢'
            elif u.groups.filter(name='Entrenadores').exists():
                role_name = 'Entrenador'
                role_badge_class = 'badge-info'
                role_icon = '🔵'
            elif u.is_staff:
                role_name = 'Personal Staff'
                role_badge_class = 'badge-warning'
                role_icon = '🟡'
            else:
                role_name = 'Usuario Estándar'
                role_badge_class = 'badge-secondary'
                role_icon = '⚪'

            users_list.append({
                'id': u.id,
                'username': u.username,
                'full_name': u.get_full_name() or u.username,
                'email': u.email or 'Sin correo',
                'role_name': role_name,
                'role_badge_class': role_badge_class,
                'role_icon': role_icon,
                'is_active': u.is_active,
                'is_superuser': u.is_superuser,
                'is_self': (u.id == self.request.user.id),
                'last_login': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else 'Nunca',
                'date_joined': u.date_joined.strftime('%d/%m/%Y'),
                'initials': (u.first_name[:1] + u.last_name[:1]).upper() if (u.first_name and u.last_name) else u.username[:2].upper()
            })
        
        context['staff_users'] = users_list
        context['roles_summary'] = {
            'admins': sum(1 for u in users_list if u['role_name'] == 'Administrador'),
            'receptionists': sum(1 for u in users_list if u['role_name'] == 'Recepcionista'),
            'trainers': sum(1 for u in users_list if u['role_name'] == 'Entrenador'),
        }
        return context

    def post(self, request, *args, **kwargs):
        settings_obj = GymSetting.get_settings()
        form = GymSettingForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Configuración del gimnasio actualizada exitosamente!")
            tab = request.POST.get('active_tab', 'tab-general')
            return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab={tab}';</script>")
        
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class PlanCreateModalView(AdminRequiredMixin, CreateView):
    """
    Creación de nuevo plan de membresía.
    """
    model = Plan
    form_class = PlanModalForm
    template_name = 'core/settings.html'

    def form_valid(self, form):
        plan = form.save()
        messages.success(self.request, f"Plan '{plan.name}' creado exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:settings') + '?tab=tab-plans'


class PlanUpdateModalView(AdminRequiredMixin, UpdateView):
    """
    Edición de plan de membresía.
    """
    model = Plan
    form_class = PlanModalForm
    template_name = 'core/settings.html'

    def form_valid(self, form):
        plan = form.save()
        messages.success(self.request, f"Plan '{plan.name}' actualizado exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:settings') + '?tab=tab-plans'


class PlanDeleteModalView(AdminRequiredMixin, DeleteView):
    """
    Eliminación de plan de membresía.
    """
    model = Plan

    def delete(self, request, *args, **kwargs):
        plan = self.get_object()
        name = plan.name
        plan.delete()
        messages.success(request, f"El plan '{name}' ha sido eliminado.")
        return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-plans';</script>")

    def get_success_url(self):
        return reverse('core:settings') + '?tab=tab-plans'


class CategoryCreateModalView(AdminRequiredMixin, CreateView):
    """
    Creación de nueva disciplina / categoría de clase.
    """
    model = ClassCategory
    form_class = CategoryModalForm
    template_name = 'core/settings.html'

    def form_valid(self, form):
        cat = form.save()
        messages.success(self.request, f"Disciplina '{cat.name}' creada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:settings') + '?tab=tab-categories'


class CategoryUpdateModalView(AdminRequiredMixin, UpdateView):
    """
    Edición de disciplina / categoría de clase.
    """
    model = ClassCategory
    form_class = CategoryModalForm
    template_name = 'core/settings.html'

    def form_valid(self, form):
        cat = form.save()
        messages.success(self.request, f"Disciplina '{cat.name}' actualizada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:settings') + '?tab=tab-categories'


class CategoryDeleteModalView(AdminRequiredMixin, DeleteView):
    """
    Eliminación de disciplina / categoría de clase.
    """
    model = ClassCategory

    def delete(self, request, *args, **kwargs):
        cat = self.get_object()
        name = cat.name
        cat.delete()
        messages.success(request, f"La disciplina '{name}' ha sido eliminada.")
        return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-categories';</script>")

    def get_success_url(self):
        return reverse('core:settings') + '?tab=tab-categories'


class BackupExportJSONView(AdminRequiredMixin, View):
    """
    Descarga una copia de seguridad estructurada en JSON de todo el gimnasio.
    """
    def get(self, request, *args, **kwargs):
        settings_obj = GymSetting.get_settings()
        
        backup_data = {
            'metadata': {
                'gym_name': settings_obj.gym_name,
                'branch_name': settings_obj.branch_name,
                'export_timestamp': timezone.now().isoformat(),
                'version': '1.0'
            },
            'settings': {
                'gym_name': settings_obj.gym_name,
                'branch_name': settings_obj.branch_name,
                'tax_id': settings_obj.tax_id,
                'address': settings_obj.address,
                'phone': settings_obj.phone,
                'whatsapp': settings_obj.whatsapp,
                'email': settings_obj.email,
                'bank_cbu': settings_obj.bank_cbu,
                'bank_alias': settings_obj.bank_alias,
                'days_advance_notice': settings_obj.days_advance_notice,
                'grace_period_days': settings_obj.grace_period_days,
                'default_class_capacity': settings_obj.default_class_capacity
            },
            'plans': [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': float(p.price),
                    'duration_days': p.duration_days,
                    'color': p.color,
                    'description': p.description,
                    'is_active': p.is_active
                }
                for p in Plan.objects.all()
            ],
            'categories': [
                {
                    'id': c.id,
                    'name': c.name,
                    'color': c.color,
                    'description': c.description
                }
                for c in ClassCategory.objects.all()
            ],
            'trainers': [
                {
                    'id': t.id,
                    'full_name': t.full_name,
                    'specialty': t.specialty,
                    'email': t.email,
                    'phone': t.phone,
                    'is_active': t.is_active
                }
                for t in Trainer.objects.all()
            ],
            'members': [
                {
                    'id': m.id,
                    'first_name': m.first_name,
                    'last_name': m.last_name,
                    'dni': m.dni,
                    'email': m.email,
                    'phone': m.phone,
                    'plan': m.plan.name if m.plan else None,
                    'status': m.status,
                    'start_date': m.start_date.isoformat() if m.start_date else None,
                    'end_date': m.end_date.isoformat() if m.end_date else None
                }
                for m in Member.objects.select_related('plan').all()
            ],
            'payments_summary': {
                'total_count': Payment.objects.count(),
                'completed_count': Payment.objects.filter(status='COMPLETADO').count(),
                'total_amount_collected': float(sum(p.amount for p in Payment.objects.filter(status='COMPLETADO')))
            }
        }

        json_str = json.dumps(backup_data, indent=2, ensure_ascii=False)
        filename = f"vitalis_backup_{timezone.now().strftime('%Y%m%d_%H%M')}.json"
        
        response = HttpResponse(json_str, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class UserCreateModalView(AdminRequiredMixin, View):
    """
    Crea un nuevo usuario empleado con rol predefinido (Administrador, Recepcionista, Entrenador).
    """
    def post(self, request, *args, **kwargs):
        admin_group, recep_group, trainer_group = get_or_create_staff_groups()
        
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'receptionist')
        is_active = request.POST.get('is_active') == 'on'

        if not username or not password:
            messages.error(request, "El nombre de usuario y la contraseña son obligatorios.")
            return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")

        if User.objects.filter(username=username).exists():
            messages.error(request, f"El nombre de usuario '{username}' ya está en uso. Por favor elige otro.")
            return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_staff=True
        )

        if role == 'admin':
            user.is_superuser = True
            user.groups.add(admin_group)
        elif role == 'receptionist':
            user.is_superuser = False
            user.groups.add(recep_group)
        elif role == 'trainer':
            user.is_superuser = False
            user.groups.add(trainer_group)

        user.save()
        messages.success(request, f"¡Empleado '{user.get_full_name() or user.username}' creado con rol {role.title()} exitosamente!")
        return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")


class UserToggleStatusModalView(AdminRequiredMixin, View):
    """
    Activa o desactiva la cuenta de un empleado.
    """
    def post(self, request, pk, *args, **kwargs):
        if request.user.id == pk:
            messages.error(request, "No puedes desactivar tu propia cuenta en sesión.")
            return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")

        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            estado = "activada" if user.is_active else "desactivada"
            messages.success(request, f"La cuenta de '{user.username}' ha sido {estado}.")
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")

        return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")


class UserDeleteModalView(AdminRequiredMixin, View):
    """
    Elimina la cuenta de un empleado (bloqueando auto-eliminación).
    """
    def post(self, request, pk, *args, **kwargs):
        if request.user.id == pk:
            messages.error(request, "No puedes eliminar tu propia cuenta de usuario.")
            return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")

        try:
            user = User.objects.get(pk=pk)
            username = user.username
            if user.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
                messages.error(request, "No puedes eliminar al único superadministrador del sistema.")
                return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")
            
            user.delete()
            messages.success(request, f"El usuario '{username}' ha sido eliminado del sistema.")
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")

        return HttpResponse(f"<script>window.location.href='{reverse('core:settings')}?tab=tab-users';</script>")
