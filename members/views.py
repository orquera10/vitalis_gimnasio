from django.contrib.auth.mixins import LoginRequiredMixin
from core.permissions import MembersManageRequiredMixin, StaffRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.utils import timezone
from .models import Member, Plan
from .forms import MemberForm


class MemberListView(StaffRequiredMixin, ListView):
    """
    Vista principal para listar, buscar y filtrar socios del gimnasio.
    """
    model = Member
    template_name = 'members/member_list.html'
    context_object_name = 'members'
    paginate_by = 15

    def get_queryset(self):
        queryset = Member.objects.select_related('plan').all()
        
        # 1. Búsqueda por término (nombre, apellido, DNI, email)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(dni__icontains=query) |
                Q(email__icontains=query)
            )

        # 2. Filtrado por Plan
        plan_id = self.request.GET.get('plan')
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)

        # 3. Filtrado por Estado
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_members = Member.objects.all()

        # Métricas de resumen de clientes
        context['metrics'] = {
            'total': all_members.count(),
            'active': all_members.filter(status='ACTIVA').count(),
            'pending': all_members.filter(status='PENDIENTE').count(),
            'expired': all_members.filter(status='VENCIDO').count(),
        }

        # Filtros disponibles
        context['plans'] = Plan.objects.filter(is_active=True)
        context['status_choices'] = Member.STATUS_CHOICES
        context['current_q'] = self.request.GET.get('q', '')
        context['current_plan'] = self.request.GET.get('plan', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context


class MemberDetailView(StaffRequiredMixin, DetailView):
    """
    Vista de perfil y ficha técnica detallada del socio con datos 360° del Portal.
    """
    model = Member
    template_name = 'members/member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object

        # Sincronizar o verificar usuario portal
        if not member.user:
            member.create_or_sync_user_account()

                # Datos del Portal de Socios (Métricas, Rutinas y PRs)
        context['portal_user'] = member.user
        context['active_routine'] = member.routines.filter(is_active=True).first() if hasattr(member, 'routines') else None
        context['recent_metrics'] = member.body_metrics.all()[:5] if hasattr(member, 'body_metrics') else []
        context['personal_records'] = member.personal_records.all()[:4] if hasattr(member, 'personal_records') else []
        return context


class MemberCreateView(MembersManageRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Vista para registrar un nuevo socio en el gimnasio con creación automática de usuario portal.
    """
    model = Member
    form_class = MemberForm
    template_name = 'members/member_form.html'
    success_url = reverse_lazy('members:list')
    success_message = "¡El socio %(first_name)s %(last_name)s ha sido registrado exitosamente y su acceso al portal fue creado!"

    def form_valid(self, form):
        response = super().form_valid(form)
        # 1. Crear / sincronizar credenciales de acceso al Portal
        self.object.create_or_sync_user_account()
        # 2. Inicializar rutina base de adaptación si no tiene
        self.object.assign_default_routine_if_none()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = "Registrar Nuevo Socio"
        context['btn_text'] = "Guardar Socio & Crear Acceso"
        return context


class MemberUpdateView(MembersManageRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Vista para actualizar la información de un socio existente.
    """
    model = Member
    form_class = MemberForm
    template_name = 'members/member_form.html'
    success_url = reverse_lazy('members:list')
    success_message = "¡La información de %(first_name)s %(last_name)s ha sido actualizada!"

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.create_or_sync_user_account()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = f"Editar Socio: {self.object.full_name}"
        context['btn_text'] = "Guardar Cambios"
        return context


class MemberDeleteView(MembersManageRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Vista para dar de baja / eliminar un socio.
    """
    model = Member
    template_name = 'members/member_confirm_delete.html'
    success_url = reverse_lazy('members:list')
    success_message = "El socio ha sido eliminado del sistema."

    def delete(self, request, *args, **kwargs):
        member = self.get_object()
        if member.user:
            member.user.is_active = False
            member.user.save()
        messages.warning(request, f"El socio {member.full_name} ha sido eliminado.")
        return super().delete(request, *args, **kwargs)


class MemberPortalResetPasswordView(MembersManageRequiredMixin, View):
    """
    Resetea la contraseña del portal para el socio a su número de DNI.
    """
    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        clean_dni = member.dni.strip().replace('.', '').replace('-', '')
        user = member.create_or_sync_user_account(default_password=clean_dni)
        messages.success(
            request,
            f"Clave de acceso al portal reseteada con éxito para {member.full_name}. Usuario: {user.username} | Clave: {clean_dni}"
        )
        return redirect('members:detail', pk=member.pk)


class KioskTerminalView(TemplateView):
    """
    Vista de pantalla completa autónoma (Kiosk Mode) para el terminal / tótem de entrada al gimnasio.
    """
    template_name = 'members/kiosk_terminal.html'


class KioskCheckInAPIView(View):
    """
    Endpoint AJAX para procesar el check-in de acceso por DNI:
    - Retorna status: 'success' si está al día (Verde)
    - Retorna status: 'expired' si venció su membresía (Rojo)
    - Retorna status: 'pending' si tiene pago pendiente (Ámbar)
    - Retorna status: 'not_found' si el DNI no está registrado
    """
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        from django.db.models import Q
        from .models import MemberCheckIn

        raw_dni = request.POST.get('dni', '').strip()
        if not raw_dni:
            return JsonResponse({'status': 'error', 'message': 'Por favor ingresa un número de DNI válido.'}, status=400)

        # Normalizar DNI para búsqueda flexible (con o sin puntos/guiones)
        clean_dni = raw_dni.replace('.', '').replace('-', '').replace(' ', '')

        member = Member.objects.filter(
            Q(dni__iexact=raw_dni) |
            Q(dni__icontains=clean_dni)
        ).first()

        if not member:
            return JsonResponse({
                'status': 'not_found',
                'title': 'DNI No Registrado',
                'message': f'El documento "{raw_dni}" no figura en el sistema. Por favor acércate a recepción.',
            })

        today = timezone.now().date()
        is_expired = False
        if member.end_date and member.end_date < today:
            is_expired = True
        elif member.status == 'VENCIDO':
            is_expired = True

        # 1. Caso: Membresía Vencida (Pantalla Roja)
        if is_expired:
            MemberCheckIn.objects.create(
                member=member,
                status='VENCIDO',
                notes='Intento de acceso con membresía vencida'
            )
            return JsonResponse({
                'status': 'expired',
                'title': 'Membresía Vencida',
                'member_name': member.full_name,
                'avatar_url': member.avatar_url,
                'plan_name': member.plan.name if member.plan else 'Sin Plan',
                'end_date': member.end_date.strftime('%d/%m/%Y') if member.end_date else 'Vencida',
                'message': f'Tu plan venció el {member.end_date.strftime("%d/%m/%Y") if member.end_date else "anteriormente"}. Por favor acércate a recepción para regularizar tu cuota.',
            })

        # 2. Caso: Estado Pendiente o Inactivo
        if member.status == 'PENDIENTE':
            MemberCheckIn.objects.create(
                member=member,
                status='PENDIENTE',
                notes='Intento de acceso con cuota pendiente'
            )
            return JsonResponse({
                'status': 'pending',
                'title': 'Cuota Pendiente de Pago',
                'member_name': member.full_name,
                'avatar_url': member.avatar_url,
                'plan_name': member.plan.name if member.plan else 'Cuota',
                'message': 'Tienes una cuota registrada pendiente de cobro. Consulta en recepción.',
            })

        if member.status == 'INACTIVA':
            MemberCheckIn.objects.create(
                member=member,
                status='INACTIVO',
                notes='Intento de acceso socio inactivo'
            )
            return JsonResponse({
                'status': 'inactive',
                'title': 'Socio Inactivo',
                'member_name': member.full_name,
                'avatar_url': member.avatar_url,
                'message': 'Tu membresía se encuentra inactiva. Por favor consulta en recepción.',
            })

        # 3. Caso Exitoso: Membresía Al Día (Pantalla Verde)
        days_left = (member.end_date - today).days if member.end_date else 30
        MemberCheckIn.objects.create(
            member=member,
            status='PERMITIDO',
            notes='Ingreso registrado por terminal kiosko'
        )

        return JsonResponse({
            'status': 'success',
            'title': f'¡Bienvenido/a, {member.first_name}!',
            'member_name': member.full_name,
            'avatar_url': member.avatar_url,
            'plan_name': member.plan.name if member.plan else 'Membresía Activa',
            'end_date': member.end_date.strftime('%d/%m/%Y') if member.end_date else '',
            'days_left': max(0, days_left),
            'message': 'Acceso registrado correctamente. ¡Que tengas un excelente entrenamiento!',
        })
