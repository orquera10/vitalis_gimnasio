from django.contrib.auth.mixins import LoginRequiredMixin
from core.permissions import MembersManageRequiredMixin, StaffRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q
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


