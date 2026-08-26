from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import date, timedelta
import json

from members.models import Member
from classes.models import ClassSession, ClassBooking
from .models import (
    WorkoutRoutine,
    RoutineDay,
    RoutineExercise,
    BodyMetric,
    PersonalRecord,
    MemberActivityDay
)
from .forms import BodyMetricForm, PortalLoginForm


class PortalLoginView(View):
    """
    Vista de inicio de sesión exclusiva para Socios / Clientes de Vitalis Fitness.
    Permite autenticar con DNI, nombre de usuario o email.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('portal:home')
        form = PortalLoginForm()
        return render(request, 'portal/login.html', {'form': form})

    def post(self, request):
        form = PortalLoginForm(request.POST)
        if form.is_valid():
            raw_ident = form.cleaned_data['username_or_dni'].strip()
            clean_dni = raw_ident.replace('.', '').replace('-', '')
            password = form.cleaned_data['password']

            # Intentar autenticar por username (DNI limpio)
            user = authenticate(request, username=clean_dni, password=password)
            if not user:
                # Intentar por username original
                user = authenticate(request, username=raw_ident, password=password)
            if not user:
                # Buscar por email
                member = Member.objects.filter(email__iexact=raw_ident).first()
                if member and member.user:
                    user = authenticate(request, username=member.user.username, password=password)
            if not user:
                # Buscar por DNI exacto
                member = Member.objects.filter(dni=raw_ident).first()
                if member and member.user:
                    user = authenticate(request, username=member.user.username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"¡Hola de nuevo, {user.first_name or user.username}!")
                    return redirect('portal:home')
                else:
                    messages.error(request, "Tu cuenta de socio se encuentra temporalmente inactiva. Consulta en recepción.")
            else:
                messages.error(request, "DNI o contraseña incorrectos. Recuerda que tu clave inicial es tu DNI.")

        return render(request, 'portal/login.html', {'form': form})


class PortalLogoutView(LogoutView):
    """
    Cierre de sesión para el portal de socios con redirección a su propio login.
    """
    next_page = reverse_lazy('portal:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Has cerrado tu sesión en el Portal de Socios.")
        return super().dispatch(request, *args, **kwargs)


def get_active_member(request):
    """
    Obtiene el socio asociado al usuario logueado o mediante selector de preview para administradores/entrenadores.
    """
    # 1. Si se pasa parámetro socio_id en GET (para staff o preview)
    socio_id = request.GET.get('socio_id')
    if socio_id:
        member = Member.objects.filter(pk=socio_id).first()
        if member:
            request.session['preview_socio_id'] = member.id
            return member
    elif request.session.get('preview_socio_id') and (request.user.is_staff or not request.user.is_authenticated):
        member = Member.objects.filter(pk=request.session.get('preview_socio_id')).first()
        if member:
            return member

    # 2. Si el usuario está autenticado y tiene perfil de socio vinculado
    if request.user.is_authenticated:
        if hasattr(request.user, 'member_profile') and request.user.member_profile:
            return request.user.member_profile
        member = Member.objects.filter(user=request.user).first()
        if member:
            return member
        member = Member.objects.filter(dni=request.user.username).first()
        if member:
            return member
        member = Member.objects.filter(email=request.user.email).first()
        if member:
            return member

    # 3. Demo default: Martín Fuentes o primer socio disponible
    martin = Member.objects.filter(dni="38492019").first()
    if martin:
        return martin
    return Member.objects.first()


class PortalDashboardView(LoginRequiredMixin, TemplateView):
    """
    Pantalla 1: Mi Panel (vitalis-client-home Figma)
    """
    template_name = 'portal/home.html'
    login_url = reverse_lazy('portal:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_active_member(self.request)
        today = timezone.now().date()

        context['member'] = member
        context['today'] = today
        context['active_tab'] = 'panel'
        context['all_members'] = Member.objects.all()

        # 1. KPIs
        latest_weight = "78.5 kg"
        if member:
            last_metric = member.body_metrics.order_by('-date').first()
            if last_metric:
                latest_weight = f"{last_metric.weight_kg} kg"

        context['kpis'] = {
            'days_trained': {
                'value': '18 / 30',
                'subtext': 'Objetivo mensual al 60%',
            },
            'streak': {
                'value': '5 Días',
                'subtext': '¡Sigue así, batiste tu récord!',
            },
            'next_class': {
                'value': '18:00',
                'subtext': 'Crossfit con Lucas Torres',
            },
            'current_weight': {
                'value': latest_weight,
                'subtext': '-2.3 kg vs mes inicial',
            }
        }

        # 2. Rutina de Hoy (Lunes / Empuje)
        today_routine = None
        if member:
            routine = member.routines.filter(is_active=True).first()
            if routine:
                today_routine = routine.days.first()
        context['today_routine_day'] = today_routine

        # 3. Clases de Hoy
        classes_today = ClassSession.objects.filter(date=today).select_related('trainer', 'category').order_by('start_time')
        booked_session_ids = set()
        if member:
            booked_session_ids = set(
                ClassBooking.objects.filter(member=member, session__date=today).values_list('session_id', flat=True)
            )

        classes_info = []
        for cs in classes_today:
            is_booked = cs.id in booked_session_ids
            status_badge = "Disponible"
            if is_booked:
                status_badge = "Reservado"
            elif cs.available_spots <= 0:
                status_badge = "Completo"

            classes_info.append({
                'session': cs,
                'time': cs.start_time.strftime('%H:%M'),
                'title': cs.title,
                'trainer_name': cs.trainer.full_name if cs.trainer else 'Staff',
                'status_badge': status_badge,
                'is_booked': is_booked
            })

        if not classes_info:
            classes_info = [
                {'time': '08:00', 'title': 'Spinning Pro', 'trainer_name': 'Mario Ruiz', 'status_badge': 'Realizado'},
                {'time': '18:00', 'title': 'Crossfit WOD', 'trainer_name': 'Lucas Torres', 'status_badge': 'Reservado'},
                {'time': '19:30', 'title': 'Power Yoga Flow', 'trainer_name': 'Ana Sofía', 'status_badge': 'Disponible'},
            ]
        context['classes_info'] = classes_info

        # 4. Calendario de Actividad Semanal
        activity_days = []
        start_week = today - timedelta(days=today.weekday())
        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for i in range(7):
            d = start_week + timedelta(days=i)
            is_trained = i in [0, 1, 3, 4]
            activity_days.append({
                'day_name': day_names[i],
                'day_number': d.day,
                'status': 'ENTRENADO' if is_trained else 'DESCANSO'
            })
        context['activity_days'] = activity_days

        return context


class PortalRoutineView(LoginRequiredMixin, TemplateView):
    """
    Pantalla 2: Mi Rutina (vitalis-client-routine Figma)
    """
    template_name = 'portal/routine.html'
    login_url = reverse_lazy('portal:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_active_member(self.request)
        context['member'] = member
        context['active_tab'] = 'rutina'
        context['all_members'] = Member.objects.all()

        routine = None
        if member:
            routine = member.routines.filter(is_active=True).first()
        context['routine'] = routine

        selected_day_name = self.request.GET.get('dia', 'Lunes')
        selected_day = None
        if routine:
            selected_day = routine.days.filter(day_name__iexact=selected_day_name).first()
            if not selected_day:
                selected_day = routine.days.first()

        context['selected_day'] = selected_day
        context['selected_day_name'] = selected_day.day_name if selected_day else 'Lunes'
        return context


class PortalProgressView(LoginRequiredMixin, TemplateView):
    """
    Pantalla 3: Mis Avances y Métricas (vitalis-client-progress Figma)
    """
    template_name = 'portal/progress.html'
    login_url = reverse_lazy('portal:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_active_member(self.request)
        context['member'] = member
        context['active_tab'] = 'avances'
        context['all_members'] = Member.objects.all()
        context['metric_form'] = BodyMetricForm()

        metrics = []
        prs = []
        if member:
            metrics = member.body_metrics.order_by('-date')
            prs = member.personal_records.all()

        context['metrics'] = metrics
        context['personal_records'] = prs

        # Estadísticas principales
        last_m = metrics.first() if metrics.exists() else None
        context['stats'] = {
            'weight': last_m.weight_kg if last_m else '78.5',
            'fat': last_m.body_fat_pct if last_m and last_m.body_fat_pct else '18.2',
            'muscle': last_m.muscle_mass_kg if last_m and last_m.muscle_mass_kg else '42.1',
            'weight_change': '-2.3 kg Meta',
            'fat_change': '-1.5% Evolución',
            'muscle_change': '+1.8 kg Ganancia',
        }

        # Datos para el gráfico Canvas
        chart_data = []
        if metrics.exists():
            for m in reversed(metrics[:6]):
                chart_data.append({
                    'date': m.date.strftime('%d %b'),
                    'weight': float(m.weight_kg)
                })
        else:
            chart_data = [
                {'date': '01 Jun', 'weight': 80.8},
                {'date': '15 Jun', 'weight': 80.1},
                {'date': '01 Jul', 'weight': 79.4},
                {'date': '15 Jul', 'weight': 79.0},
                {'date': 'Hoy', 'weight': 78.5}
            ]
        context['chart_data_json'] = json.dumps(chart_data)

        return context


class PortalAddMetricView(LoginRequiredMixin, View):
    """
    Procesa el formulario modal de registro de nueva métrica corporal.
    """
    login_url = reverse_lazy('portal:login')

    def post(self, request):
        member = get_active_member(request)
        form = BodyMetricForm(request.POST)
        if form.is_valid():
            metric = form.save(commit=False)
            metric.member = member
            metric.save()
            messages.success(request, f"¡Nueva medición de {metric.weight_kg} kg registrada correctamente!")
        else:
            messages.error(request, "Error al guardar la métrica. Verifica los datos ingresados.")
        return redirect('portal:progress')


class PortalProfileView(LoginRequiredMixin, TemplateView):
    """
    Pantalla 4: Carnet Digital VIP y Perfil del Socio.
    """
    template_name = 'portal/profile.html'
    login_url = reverse_lazy('portal:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_active_member(self.request)
        context['member'] = member
        context['active_tab'] = 'perfil'
        context['all_members'] = Member.objects.all()
        context['qr_code_value'] = f"VITALIS-VIP-{member.dni if member else '38492019'}-VALID"
        return context


class PortalBookClassToggleView(LoginRequiredMixin, View):
    """
    Reserva o cancela cupo en una clase desde el portal.
    """
    login_url = reverse_lazy('portal:login')

    def post(self, request, session_id):
        member = get_active_member(request)
        session = get_object_or_404(ClassSession, id=session_id)

        booking = ClassBooking.objects.filter(session=session, member=member).first()
        if booking:
            booking.delete()
            messages.info(request, f"Has cancelado tu reserva para {session.title}.")
        else:
            if session.available_spots > 0:
                ClassBooking.objects.create(session=session, member=member, status="CONFIRMADO")
                messages.success(request, f"¡Reserva confirmada para {session.title} a las {session.start_time.strftime('%H:%M')}!")
            else:
                messages.error(request, "Lo sentimos, no quedan cupos disponibles para esta clase.")

        return redirect('portal:home')
