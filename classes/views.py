from django.contrib.auth.mixins import LoginRequiredMixin
from core.permissions import MembersManageRequiredMixin, StaffRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, ListView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from django.db.models import Q, Count
from members.models import Member
from .models import ClassSession, ClassSchedule, Trainer, ClassCategory, ClassBooking
from .forms import ClassScheduleForm, ClassSessionForm, ClassBookingForm, TrainerForm


class ClassCalendarView(StaffRequiredMixin, TemplateView):
    """
    Vista principal del Almanaque / Calendario Semanal y Mensual de Clases.
    """
    template_name = 'classes/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Determinar fecha de referencia
        ref_date_str = self.request.GET.get('date')
        if ref_date_str:
            try:
                current_date = datetime.strptime(ref_date_str, '%Y-%m-%d').date()
            except ValueError:
                current_date = timezone.now().date()
        else:
            current_date = timezone.now().date()

        # 2. Calcular inicio de semana (Lunes = 0)
        start_of_week = current_date - timedelta(days=current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # 3. Crear lista de los 7 dÃ­as de la semana
        week_days = []
        spanish_days = ['Lunes', 'Martes', 'MiÃ©rcoles', 'Jueves', 'Viernes', 'SÃ¡bado', 'Domingo']
        
        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            week_days.append({
                'date': day_date,
                'name': spanish_days[i],
                'day_num': day_date.day,
                'is_today': (day_date == timezone.now().date()),
                'day_of_week': i + 1,
            })

        # 4. Obtener sesiones de la semana con filtros
        sessions = ClassSession.objects.filter(
            date__range=[start_of_week, end_of_week]
        ).select_related('trainer', 'category').order_by('date', 'start_time')

        # Filtro opcional por categorÃ­a / disciplina
        category_id = self.request.GET.get('category')
        if category_id:
            sessions = sessions.filter(category_id=category_id)

        # Filtro opcional por entrenador
        trainer_id = self.request.GET.get('trainer')
        if trainer_id:
            sessions = sessions.filter(trainer_id=trainer_id)

        # 5. Agrupar sesiones por fecha
        sessions_by_date = {day['date']: [] for day in week_days}
        for s in sessions:
            if s.date in sessions_by_date:
                sessions_by_date[s.date].append(s)

        # AÃ±adir las sesiones correspondientes a cada dÃ­a
        for day in week_days:
            day['sessions'] = sessions_by_date.get(day['date'], [])

        # 6. MÃ©tricas y datos de contexto
        all_schedules = ClassSchedule.objects.filter(is_active=True).select_related('trainer', 'category')
        
        context['week_days'] = week_days
        context['start_of_week'] = start_of_week
        context['end_of_week'] = end_of_week
        context['prev_week'] = (start_of_week - timedelta(days=7)).strftime('%Y-%m-%d')
        context['next_week'] = (start_of_week + timedelta(days=7)).strftime('%Y-%m-%d')
        context['today_str'] = timezone.now().date().strftime('%Y-%m-%d')
        context['categories'] = ClassCategory.objects.all()
        context['trainers'] = Trainer.objects.filter(is_active=True)
        context['current_category'] = category_id or ''
        context['current_trainer'] = trainer_id or ''
        context['schedules'] = all_schedules
        context['total_week_classes'] = sessions.count()

        return context


class ClassScheduleCreateView(MembersManageRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Vista para crear un horario recurrente (ej. Funcional MiÃ©rcoles y Viernes de 20:00 a 22:00)
    y generar automÃ¡ticamente las sesiones de las prÃ³ximas semanas.
    """
    model = ClassSchedule
    form_class = ClassScheduleForm
    template_name = 'classes/schedule_form.html'
    success_url = reverse_lazy('classes:calendar')
    success_message = "Â¡El horario recurrente ha sido registrado y programado en el almanaque!"

    def form_valid(self, form):
        selected_days = form.cleaned_data.get('selected_days', [])
        schedule_title = form.cleaned_data.get('title')
        category = form.cleaned_data.get('category')
        trainer = form.cleaned_data.get('trainer')
        start_time = form.cleaned_data.get('start_time')
        end_time = form.cleaned_data.get('end_time')
        room = form.cleaned_data.get('room')
        capacity = form.cleaned_data.get('capacity')
        is_active = form.cleaned_data.get('is_active', True)

        # Crear un ClassSchedule por cada dÃ­a seleccionado
        first_schedule = None
        for day in selected_days:
            day_num = int(day)
            sch = ClassSchedule.objects.create(
                title=schedule_title,
                category=category,
                trainer=trainer,
                day_of_week=day_num,
                start_time=start_time,
                end_time=end_time,
                room=room,
                capacity=capacity,
                is_active=is_active
            )
            if not first_schedule:
                first_schedule = sch

            # Generar automÃ¡ticamente sesiones para las prÃ³ximas 4 semanas en ese dÃ­a
            today = timezone.now().date()
            for week in range(4):
                # Calcular la fecha correspondiente al dÃ­a de la semana
                days_ahead = (day_num - 1) - today.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                session_date = today + timedelta(days=days_ahead + (week * 7))

                ClassSession.objects.get_or_create(
                    schedule=sch,
                    date=session_date,
                    start_time=start_time,
                    defaults={
                        'title': schedule_title,
                        'category': category,
                        'trainer': trainer,
                        'end_time': end_time,
                        'room': room,
                        'capacity': capacity,
                        'booked_count': 0,
                        'status': 'PROGRAMADA'
                    }
                )

        messages.success(self.request, f"Â¡Clase '{schedule_title}' programada para los dÃ­as seleccionados exitosamente!")
        return redirect('classes:calendar')


class ClassSessionCreateView(MembersManageRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Vista para programar una sesiÃ³n de clase puntual en una fecha especÃ­fica.
    """
    model = ClassSession
    form_class = ClassSessionForm
    template_name = 'classes/session_form.html'
    success_url = reverse_lazy('classes:calendar')
    success_message = "Â¡La sesiÃ³n de clase ha sido agendada en el almanaque!"

    def get_initial(self):
        initial = super().get_initial()
        date_str = self.request.GET.get('date')
        if date_str:
            initial['date'] = date_str
        return initial


class ClassDetailView(StaffRequiredMixin, DetailView):
    """
    Detalle de una sesiÃ³n de clase puntual, lista de inscriptos y formulario de inscripciÃ³n.
    """
    model = ClassSession
    template_name = 'classes/class_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        
        # Lista de inscriptos
        bookings = session.bookings.select_related('member', 'member__plan').order_by('-booking_date')
        context['bookings'] = bookings
        
        # Formulario de inscripciÃ³n
        context['booking_form'] = ClassBookingForm()
        
        # Porcentaje de ocupaciÃ³n
        if session.capacity > 0:
            context['occupancy_pct'] = min(100, int((session.booked_count / session.capacity) * 100))
        else:
            context['occupancy_pct'] = 0

        # Socios ya inscriptos para excluir del select
        context['enrolled_member_ids'] = list(session.bookings.values_list('member_id', flat=True))

        return context


class ClassBookingCreateView(StaffRequiredMixin, View):
    """
    Inscribir un socio activo a la sesiÃ³n de clase.
    """
    def post(self, request, pk, *args, **kwargs):
        session = get_object_or_404(ClassSession, pk=pk)

        # 1. Validar que la clase no estÃ© llena
        if session.is_full:
            messages.error(request, "âŒ No hay cupos disponibles. La clase se encuentra llena.")
            return redirect('classes:detail', pk=session.pk)

        # 2. Obtener y validar el socio
        member_id = request.POST.get('member')
        if not member_id:
            messages.error(request, "Por favor, selecciona un socio vÃ¡lido.")
            return redirect('classes:detail', pk=session.pk)

        member = get_object_or_404(Member, pk=member_id)

        # 3. Validar estado de la membresÃ­a del socio
        if member.status != 'ACTIVA':
            messages.error(request, f"âŒ El socio {member.full_name} no posee membresÃ­a ACTIVA (Estado actual: {member.get_status_display()}).")
            return redirect('classes:detail', pk=session.pk)

        # 4. Validar duplicidad
        if ClassBooking.objects.filter(session=session, member=member).exists():
            messages.warning(request, f"âš ï¸ El socio {member.full_name} ya se encuentra inscripto en esta clase.")
            return redirect('classes:detail', pk=session.pk)

        # 5. Crear la inscripciÃ³n
        notes = request.POST.get('notes', '').strip()
        ClassBooking.objects.create(
            session=session,
            member=member,
            notes=notes,
            status='RESERVADO'
        )

        messages.success(request, f"âœ… Â¡{member.full_name} ha sido inscripto exitosamente en '{session.title}'!")
        return redirect('classes:detail', pk=session.pk)


class ClassBookingStatusUpdateView(StaffRequiredMixin, View):
    """
    Actualizar estado de asistencia (Presente, Ausente, Reservado) de un socio inscripto.
    """
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(ClassBooking, pk=pk)
        new_status = request.POST.get('status')
        
        valid_statuses = dict(ClassBooking.STATUS_CHOICES)
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save()
            messages.success(request, f"Asistencia de {booking.member.full_name} actualizada a: {valid_statuses[new_status]}.")
        else:
            messages.error(request, "Estado de asistencia no vÃ¡lido.")

        return redirect('classes:detail', pk=booking.session.pk)


class ClassBookingDeleteView(StaffRequiredMixin, View):
    """
    Dar de baja la inscripciÃ³n de un socio, liberando automÃ¡ticamente el cupo.
    """
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(ClassBooking, pk=pk)
        session_pk = booking.session.pk
        member_name = booking.member.full_name
        booking.delete()
        messages.warning(request, f"ðŸ—‘ï¸ Se cancelÃ³ la inscripciÃ³n de {member_name}. Se ha liberado 1 cupo.")
        return redirect('classes:detail', pk=session_pk)


class ClassSessionDeleteView(StaffRequiredMixin, DeleteView):
    """
    Cancelar o eliminar una sesiÃ³n de clase puntual.
    """
    model = ClassSession
    success_url = reverse_lazy('classes:calendar')

    def delete(self, request, *args, **kwargs):
        session = self.get_object()
        messages.warning(request, f"La sesiÃ³n de '{session.title}' del {session.date.strftime('%d/%m/%Y')} ha sido cancelada.")
        return super().delete(request, *args, **kwargs)


# ==========================================
# VISTAS DE ENTRENADORES / INSTRUCTORES
# ==========================================

class TrainerListView(StaffRequiredMixin, ListView):
    """
    Lista y directorio de entrenadores / instructores de Vitalis Fitness.
    """
    model = Trainer
    template_name = 'classes/trainer_list.html'
    context_object_name = 'trainers'
    paginate_by = 12

    def get_queryset(self):
        queryset = Trainer.objects.annotate(
            schedules_count=Count('schedules', distinct=True),
            sessions_count=Count('sessions', distinct=True)
        ).order_by('first_name', 'last_name')

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(specialty__icontains=q) |
                Q(email__icontains=q)
            )

        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['total_trainers'] = Trainer.objects.count()
        context['active_trainers'] = Trainer.objects.filter(is_active=True).count()
        return context


class TrainerCreateView(MembersManageRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Registrar un nuevo entrenador / instructor.
    """
    model = Trainer
    form_class = TrainerForm
    template_name = 'classes/trainer_form.html'
    success_url = reverse_lazy('classes:trainer_list')
    success_message = "Â¡Entrenador registrado exitosamente en el staff!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context


class TrainerDetailView(StaffRequiredMixin, DetailView):
    """
    Ficha de perfil del entrenador con sus clases recurrentes y prÃ³ximas sesiones.
    """
    model = Trainer
    template_name = 'classes/trainer_detail.html'
    context_object_name = 'trainer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainer = self.get_object()
        today = timezone.now().date()

        context['schedules'] = trainer.schedules.filter(is_active=True).select_related('category')
        context['upcoming_sessions'] = trainer.sessions.filter(
            date__gte=today
        ).select_related('category').order_by('date', 'start_time')[:8]
        
        # Total de asistencias confirmadas que ha dirigido
        context['total_students_attended'] = ClassBooking.objects.filter(
            session__trainer=trainer,
            status='PRESENTE'
        ).count()

        return context


class TrainerUpdateView(MembersManageRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Editar datos de un entrenador / instructor.
    """
    model = Trainer
    form_class = TrainerForm
    template_name = 'classes/trainer_form.html'
    success_message = "Â¡Datos del entrenador actualizados exitosamente!"

    def get_success_url(self):
        return reverse_lazy('classes:trainer_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class TrainerDeleteView(MembersManageRequiredMixin, DeleteView):
    """
    Eliminar o dar de baja a un entrenador.
    """
    model = Trainer
    success_url = reverse_lazy('classes:trainer_list')

    def delete(self, request, *args, **kwargs):
        trainer = self.get_object()
        messages.warning(request, f"El entrenador '{trainer.full_name}' ha sido eliminado del staff.")
        return super().delete(request, *args, **kwargs)

