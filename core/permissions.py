from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


def is_staff_or_admin_user(user):
    """
    Verifica si el usuario pertenece al personal del gimnasio (Staff, Superusuario, Admin, Recepcionista, Entrenador).
    Los socios estándar retornan False.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=['Administradores', 'Recepcionistas', 'Entrenadores']).exists()


def is_admin_user(user):
    """Verifica si el usuario es Superusuario o pertenece al grupo Administradores."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Administradores').exists()


def is_receptionist_user(user):
    """Verifica si el usuario pertenece al grupo Recepcionistas."""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Recepcionistas').exists()


def is_trainer_user(user):
    """Verifica si el usuario pertenece al grupo Entrenadores."""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Entrenadores').exists()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe el acceso al panel administrativo y datos de la empresa exclusivamente a personal del gimnasio.
    Los socios son redirigidos automáticamente al Portal de Socios.
    """
    def test_func(self):
        return is_staff_or_admin_user(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.info(self.request, "Tu cuenta de socio tiene acceso exclusivo a tu Portal de Clientes.")
            return redirect('portal:home')
        return super().handle_no_permission()


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe el acceso exclusivamente a usuarios con rol Administrador o Superusuario.
    """
    def test_func(self):
        return is_admin_user(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if not is_staff_or_admin_user(self.request.user):
                messages.info(self.request, "Tu cuenta de socio tiene acceso exclusivo a tu Portal de Clientes.")
                return redirect('portal:home')
            messages.error(self.request, "Acceso Restringido: Se requieren permisos de Administrador para acceder a esta sección.")
            return redirect('core:home')
        return super().handle_no_permission()


class PaymentsAccessRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe el acceso al módulo de Pagos & Cobranzas a Administradores y Recepcionistas.
    """
    def test_func(self):
        user = self.request.user
        return is_admin_user(user) or is_receptionist_user(user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if not is_staff_or_admin_user(self.request.user):
                messages.info(self.request, "Tu cuenta de socio tiene acceso exclusivo a tu Portal de Clientes.")
                return redirect('portal:home')
            messages.error(self.request, "Acceso Denegado: Tu rol de usuario no tiene permisos para acceder al módulo de Pagos y Finanzas.")
            return redirect('core:home')
        return super().handle_no_permission()


class MembersManageRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe la creación, edición y eliminación de socios a Administradores y Recepcionistas.
    """
    def test_func(self):
        user = self.request.user
        return is_admin_user(user) or is_receptionist_user(user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if not is_staff_or_admin_user(self.request.user):
                messages.info(self.request, "Tu cuenta de socio tiene acceso exclusivo a tu Portal de Clientes.")
                return redirect('portal:home')
            messages.error(self.request, "Acceso Denegado: Tu rol no tiene permisos para dar de alta o modificar socios.")
            return redirect('members:list')
        return super().handle_no_permission()
