import csv
from datetime import datetime, date, timedelta
from decimal import Decimal
from core.permissions import AdminRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from members.models import Member, Plan
from classes.models import ClassSession, ClassBooking, ClassCategory, Trainer
from payments.models import Payment


class ReportsDashboardView(AdminRequiredMixin, TemplateView):
    """
    Centro de reportería y analíticas ejecutivas de Vitalis Fitness.
    """
    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # 1. Rango de Fechas
        preset = self.request.GET.get('preset', 'this_month')
        date_from_str = self.request.GET.get('date_from')
        date_to_str = self.request.GET.get('date_to')

        if date_from_str and date_to_str:
            try:
                start_date = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                preset = 'custom'
            except ValueError:
                start_date = today.replace(day=1)
                end_date = today
        elif preset == 'last_month':
            first_this_month = today.replace(day=1)
            end_date = first_this_month - timedelta(days=1)
            start_date = end_date.replace(day=1)
        elif preset == 'last_3_months':
            start_date = today - timedelta(days=90)
            end_date = today
        elif preset == 'this_year':
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
        elif preset == 'all_time':
            start_date = date(2020, 1, 1)
            end_date = today + timedelta(days=365)
        else:  # this_month (por defecto)
            preset = 'this_month'
            start_date = today.replace(day=1)
            # Fin de mes actual
            if today.month == 12:
                end_date = date(today.year, 12, 31)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

        context['start_date'] = start_date
        context['end_date'] = end_date
        context['current_preset'] = preset

        # -------------------------------------------------------------
        # 2. ANALÍTICA FINANCIERA (payments)
        # -------------------------------------------------------------
        payments_qs = Payment.objects.filter(payment_date__range=[start_date, end_date])
        completed_payments = payments_qs.filter(status='COMPLETADO')

        total_income = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        avg_ticket = completed_payments.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
        completed_count = completed_payments.count()

        pending_payments = payments_qs.filter(status='PENDIENTE')
        pending_income = pending_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pending_count = pending_payments.count()

        cancelled_count = payments_qs.filter(status='ANULADO').count()

        # Ingresos por Método de Pago
        methods_data = []
        for code, label in Payment.METHOD_CHOICES:
            method_sum = completed_payments.filter(payment_method=code).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            method_count = completed_payments.filter(payment_method=code).count()
            pct = (float(method_sum) / float(total_income) * 100) if total_income > 0 else 0
            methods_data.append({
                'code': code,
                'label': label,
                'total': method_sum,
                'count': method_count,
                'pct': round(pct, 1)
            })

        # Ingresos por Plan
        plans_data = []
        for plan in Plan.objects.all():
            p_sum = completed_payments.filter(plan=plan).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            p_count = completed_payments.filter(plan=plan).count()
            pct = (float(p_sum) / float(total_income) * 100) if total_income > 0 else 0
            plans_data.append({
                'name': plan.name,
                'color': plan.color,
                'total': p_sum,
                'count': p_count,
                'pct': round(pct, 1)
            })

        # Pagos sin plan asignado (cuota general)
        unassigned_sum = completed_payments.filter(plan__isnull=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        if unassigned_sum > 0:
            pct = (float(unassigned_sum) / float(total_income) * 100) if total_income > 0 else 0
            plans_data.append({
                'name': 'Cuotas Generales / Otros',
                'color': '#94a3b8',
                'total': unassigned_sum,
                'count': completed_payments.filter(plan__isnull=True).count(),
                'pct': round(pct, 1)
            })

        context['financial'] = {
            'total_income': total_income,
            'avg_ticket': avg_ticket,
            'completed_count': completed_count,
            'pending_income': pending_income,
            'pending_count': pending_count,
            'cancelled_count': cancelled_count,
            'methods': methods_data,
            'plans': plans_data,
            'recent_payments': completed_payments.select_related('member', 'plan')[:8]
        }

        # -------------------------------------------------------------
        # 3. ANALÍTICA DE SOCIOS Y RETENCIÓN (members)
        # -------------------------------------------------------------
        total_members = Member.objects.count()
        active_members = Member.objects.filter(status='ACTIVA').count()
        pending_members = Member.objects.filter(status='PENDIENTE').count()
        expired_members = Member.objects.filter(status='VENCIDA').count()
        new_members = Member.objects.filter(created_at__date__range=[start_date, end_date]).count()

        # Socios que vencen próximamente (Próximos 7, 15 y 30 días)
        expiring_7 = Member.objects.filter(status='ACTIVA', end_date__range=[today, today + timedelta(days=7)]).count()
        expiring_15 = Member.objects.filter(status='ACTIVA', end_date__range=[today, today + timedelta(days=15)]).count()
        expiring_30 = Member.objects.filter(status='ACTIVA', end_date__range=[today, today + timedelta(days=30)]).count()

        # Listado de socios que vencen en los próximos 30 días
        expiring_list = Member.objects.filter(
            status='ACTIVA',
            end_date__range=[today, today + timedelta(days=30)]
        ).select_related('plan').order_by('end_date')[:10]

        context['members_stats'] = {
            'total': total_members,
            'active': active_members,
            'pending': pending_members,
            'expired': expired_members,
            'new_signups': new_members,
            'expiring_7': expiring_7,
            'expiring_15': expiring_15,
            'expiring_30': expiring_30,
            'expiring_list': expiring_list,
        }

        # -------------------------------------------------------------
        # 4. ANALÍTICA DE CLASES Y ASISTENCIA (classes)
        # -------------------------------------------------------------
        sessions_qs = ClassSession.objects.filter(date__range=[start_date, end_date])
        total_sessions = sessions_qs.count()

        bookings_qs = ClassBooking.objects.filter(session__date__range=[start_date, end_date])
        total_bookings = bookings_qs.count()
        attended_bookings = bookings_qs.filter(status='PRESENTE').count()
        absent_bookings = bookings_qs.filter(status='AUSENTE').count()
        booked_pending = bookings_qs.filter(status='RESERVADO').count()

        attendance_rate = 0
        if (attended_bookings + absent_bookings) > 0:
            attendance_rate = round((attended_bookings / (attended_bookings + absent_bookings)) * 100, 1)

        # Ocupación por Disciplina
        categories_stats = []
        for cat in ClassCategory.objects.all():
            cat_sessions = sessions_qs.filter(category=cat)
            cat_sess_count = cat_sessions.count()
            cat_bookings = bookings_qs.filter(session__category=cat).count()
            cat_capacity = cat_sessions.aggregate(total=Sum('capacity'))['total'] or 0
            occ_pct = round((cat_bookings / cat_capacity * 100), 1) if cat_capacity > 0 else 0

            categories_stats.append({
                'name': cat.name,
                'color': cat.color,
                'sessions_count': cat_sess_count,
                'bookings_count': cat_bookings,
                'capacity': cat_capacity,
                'occupation_pct': occ_pct
            })

        # Rendimiento por Entrenador
        trainers_stats = []
        for tr in Trainer.objects.filter(is_active=True):
            tr_sessions = sessions_qs.filter(trainer=tr).count()
            tr_students = bookings_qs.filter(session__trainer=tr, status='PRESENTE').count()
            trainers_stats.append({
                'trainer': tr,
                'sessions_count': tr_sessions,
                'students_attended': tr_students
            })

        context['classes_stats'] = {
            'total_sessions': total_sessions,
            'total_bookings': total_bookings,
            'attended_bookings': attended_bookings,
            'absent_bookings': absent_bookings,
            'booked_pending': booked_pending,
            'attendance_rate': attendance_rate,
            'categories': sorted(categories_stats, key=lambda x: x['bookings_count'], reverse=True),
            'trainers': sorted(trainers_stats, key=lambda x: x['students_attended'], reverse=True),
        }

        return context


class ExportPaymentsCSVView(AdminRequiredMixin, View):
    """
    Exporta el reporte de pagos a archivo CSV compatible con Excel.
    """
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"reporte_pagos_vitalis_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # UTF-8 BOM para apertura perfecta en Excel
        response.write('\ufeff')
        writer = csv.writer(response)

        # Cabeceras
        writer.writerow([
            'N° Recibo', 'Fecha de Pago', 'Socio / Cliente', 'DNI',
            'Plan / Concepto', 'Método de Pago', 'Monto ($)', 'Estado', 'Notas'
        ])

        # Filtrar pagos
        payments = Payment.objects.select_related('member', 'plan').order_by('-payment_date', '-created_at')

        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)

        for p in payments:
            writer.writerow([
                p.invoice_number,
                p.payment_date.strftime('%d/%m/%Y'),
                p.member.full_name,
                p.member.dni,
                p.plan.name if p.plan else 'Cuota General',
                p.get_payment_method_display(),
                f"{p.amount:.2f}",
                p.get_status_display(),
                p.notes or ''
            ])

        return response


class ExportMembersCSVView(AdminRequiredMixin, View):
    """
    Exporta el listado de socios y membresías a CSV para Excel.
    """
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"reporte_socios_vitalis_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        response.write('\ufeff')
        writer = csv.writer(response)

        writer.writerow([
            'ID', 'Nombre', 'Apellido', 'DNI', 'Email', 'Teléfono',
            'Plan', 'Estado', 'Fecha Inicio', 'Fecha Vencimiento',
            'Contacto Emergencia', 'Tel. Emergencia'
        ])

        members = Member.objects.select_related('plan').order_by('last_name', 'first_name')

        status = request.GET.get('status')
        if status:
            members = members.filter(status=status)

        for m in members:
            writer.writerow([
                m.id,
                m.first_name,
                m.last_name,
                m.dni,
                m.email,
                m.phone,
                m.plan.name if m.plan else 'Sin Plan',
                m.get_status_display(),
                m.start_date.strftime('%d/%m/%Y') if m.start_date else '',
                m.end_date.strftime('%d/%m/%Y') if m.end_date else '',
                m.emergency_contact_name,
                m.emergency_contact_phone
            ])

        return response


class ExportAttendanceCSVView(AdminRequiredMixin, View):
    """
    Exporta el registro de asistencias a clases a CSV para Excel.
    """
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"reporte_asistencias_vitalis_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        response.write('\ufeff')
        writer = csv.writer(response)

        writer.writerow([
            'Fecha Clase', 'Horario', 'Disciplina', 'Clase / Título',
            'Entrenador', 'Socio', 'DNI Socio', 'Estado Asistencia', 'Notas'
        ])

        bookings = ClassBooking.objects.select_related('session__trainer', 'session__category', 'member').order_by('-session__date', 'session__start_time')

        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if date_from:
            bookings = bookings.filter(session__date__gte=date_from)
        if date_to:
            bookings = bookings.filter(session__date__lte=date_to)

        for b in bookings:
            writer.writerow([
                b.session.date.strftime('%d/%m/%Y'),
                b.session.time_range,
                b.session.category.name,
                b.session.title,
                b.session.trainer.full_name,
                b.member.full_name,
                b.member.dni,
                b.get_status_display(),
                b.notes or ''
            ])

        return response


class PrintableExecutiveReportView(AdminRequiredMixin, TemplateView):
    """
    Informe ejecutivo formal formateado para impresión o exportación en PDF.
    """
    template_name = 'reports/printable_report.html'

    def get_context_data(self, **kwargs):
        # Reutiliza el contexto completo calculado en ReportsDashboardView
        dashboard_view = ReportsDashboardView()
        dashboard_view.request = self.request
        return dashboard_view.get_context_data(**kwargs)
