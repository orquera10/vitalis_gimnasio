from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import date, timedelta
import json
from decimal import Decimal

from members.models import Member
from classes.models import ClassSession, ClassBooking
from portal.models import (
    WorkoutRoutine,
    RoutineDay,
    RoutineExercise,
    BodyMetric,
    PersonalRecord,
    MemberActivityDay
)
from portal.views import get_active_member


class ApiSocioDashboardView(View):
    """
    GET /api/v1/socio/dashboard/
    Retorna los datos completos para la pantalla inicial del socio.
    """
    def get(self, request, *args, **kwargs):
        member = get_active_member(request)
        if not member:
            return JsonResponse({"error": "Socio no encontrado"}, status=404)

        today = timezone.now().date()
        latest_metric = BodyMetric.objects.filter(member=member).order_by('-date').first()
        initial_metric = BodyMetric.objects.filter(member=member).order_by('date').first()
        weight_diff = None
        if latest_metric and initial_metric:
            diff = latest_metric.weight_kg - initial_metric.weight_kg
            weight_diff = f"{diff:+.1f} kg vs mes inicial"

        routine = WorkoutRoutine.objects.filter(member=member, is_active=True).first()
        
        # Actividad
        activities = MemberActivityDay.objects.filter(member=member).order_by('date')
        activity_list = [
            {
                "date": a.date.isoformat(),
                "day_name": a.day_name,
                "day_number": a.day_number,
                "status": a.status
            }
            for a in activities
        ]

        # Clases de hoy
        today_sessions = ClassSession.objects.filter(date=today).select_related('category', 'trainer').order_by('start_time')
        classes_data = []
        for s in today_sessions:
            booking = ClassBooking.objects.filter(session=s, member=member).first()
            classes_data.append({
                "id": s.id,
                "title": getattr(s, 'title', None) or s.category.name,
                "category": s.category.name,
                "trainer": s.trainer.full_name if s.trainer else None,
                "time": s.start_time.strftime("%H:%M") if hasattr(s.start_time, 'strftime') else str(s.start_time)[:5],
                "status": booking.status if booking else "DISPONIBLE",
                "is_booked": booking is not None and booking.status in ['RESERVADO', 'CONFIRMADO']
            })

        data = {
            "member": {
                "id": member.id,
                "name": member.full_name,
                "dni": member.dni,
                "plan": member.plan.name if member.plan else "Sin Plan",
                "avatar": member.avatar_url,
                "status": member.status
            },
            "kpis": {
                "days_trained": "18 / 30",
                "days_trained_percent": 60,
                "streak": "5 Días",
                "next_class": "18:00 Crossfit con Lucas Torres",
                "current_weight": f"{latest_metric.weight_kg} kg" if latest_metric else "78.5 kg",
                "weight_trend": weight_diff or "-2.3 kg vs mes inicial"
            },
            "today_workout": {
                "title": routine.goal if routine else "Hipertrofia de Empuje: Pecho y Tríceps",
                "routine_name": routine.name if routine else "Hipertrofia Clásica",
                "progress_percent": routine.progress_percent if routine else 38
            },
            "classes_today": classes_data,
            "weekly_activity": activity_list
        }
        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})


class ApiSocioRoutineView(View):
    """
    GET /api/v1/socio/rutina/
    Retorna la rutina completa con todos los días y ejercicios.
    """
    def get(self, request, *args, **kwargs):
        member = get_active_member(request)
        if not member:
            return JsonResponse({"error": "Socio no encontrado"}, status=404)

        routine = WorkoutRoutine.objects.filter(member=member, is_active=True).prefetch_related('days__exercises').first()
        if not routine:
            return JsonResponse({"error": "No hay rutina activa asignada"}, status=404)

        days_data = []
        for day in routine.days.all():
            exercises_data = [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "muscle_group": ex.muscle_group,
                    "series_reps": ex.series_reps,
                    "rest_seconds": ex.rest_seconds,
                    "image_url": ex.image_url,
                    "order": ex.order,
                    "notes": ex.notes
                }
                for ex in day.exercises.all()
            ]
            days_data.append({
                "id": day.id,
                "day_name": day.day_name,
                "subtitle": day.subtitle,
                "is_rest_day": day.is_rest_day,
                "order": day.order,
                "exercises": exercises_data
            })

        data = {
            "routine_id": routine.id,
            "name": routine.name,
            "goal": routine.goal,
            "total_weeks": routine.total_weeks,
            "current_week": routine.current_week,
            "progress_percent": routine.progress_percent,
            "trainer": {
                "name": routine.trainer.full_name if routine.trainer else None,
                "avatar": routine.trainer.avatar_url if routine.trainer else None
            } if routine.trainer else None,
            "trainer_notes": routine.trainer_notes,
            "days": days_data
        }
        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})


@method_decorator(csrf_exempt, name='dispatch')
class ApiSocioProgressView(View):
    """
    GET /api/v1/socio/avances/ -> Historial y PRs
    POST /api/v1/socio/avances/ -> Registrar nueva medición
    """
    def get(self, request, *args, **kwargs):
        member = get_active_member(request)
        if not member:
            return JsonResponse({"error": "Socio no encontrado"}, status=404)

        metrics = BodyMetric.objects.filter(member=member).order_by('-date')
        metrics_list = [
            {
                "id": m.id,
                "date": m.date.isoformat(),
                "weight_kg": float(m.weight_kg),
                "body_fat_pct": float(m.body_fat_pct) if m.body_fat_pct else None,
                "muscle_mass_kg": float(m.muscle_mass_kg) if m.muscle_mass_kg else None,
                "waist_cm": float(m.waist_cm) if m.waist_cm else None,
                "chest_cm": float(m.chest_cm) if m.chest_cm else None,
            }
            for m in metrics
        ]

        prs = PersonalRecord.objects.filter(member=member).order_by('order')
        prs_list = [
            {
                "id": p.id,
                "exercise_name": p.exercise_name,
                "weight_kg": float(p.weight_kg),
                "achieved_date": p.achieved_date.isoformat(),
                "badge_type": p.badge_type
            }
            for p in prs
        ]

        latest = metrics.first()
        initial = metrics.last()
        data = {
            "current_stats": {
                "weight_kg": float(latest.weight_kg) if latest else 78.5,
                "body_fat_pct": float(latest.body_fat_pct) if (latest and latest.body_fat_pct) else 18.2,
                "muscle_mass_kg": float(latest.muscle_mass_kg) if (latest and latest.muscle_mass_kg) else 42.1,
            },
            "history": metrics_list,
            "personal_records": prs_list
        }
        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})

    def post(self, request, *args, **kwargs):
        member = get_active_member(request)
        if not member:
            return JsonResponse({"error": "Socio no encontrado"}, status=404)

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        weight = body.get('weight_kg')
        if not weight:
            return JsonResponse({"error": "El peso es obligatorio"}, status=400)

        metric = BodyMetric.objects.create(
            member=member,
            date=body.get('date') or timezone.now().date(),
            weight_kg=Decimal(str(weight)),
            body_fat_pct=Decimal(str(body.get('body_fat_pct'))) if body.get('body_fat_pct') else None,
            muscle_mass_kg=Decimal(str(body.get('muscle_mass_kg'))) if body.get('muscle_mass_kg') else None,
            waist_cm=Decimal(str(body.get('waist_cm'))) if body.get('waist_cm') else None,
            chest_cm=Decimal(str(body.get('chest_cm'))) if body.get('chest_cm') else None,
            notes=body.get('notes', '')
        )

        return JsonResponse({
            "status": "success",
            "message": "Métrica registrada con éxito",
            "metric_id": metric.id,
            "weight_kg": float(metric.weight_kg)
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class ApiSocioClassBookingView(View):
    """
    POST /api/v1/socio/clases/<id>/reservar/ -> Reservar o cancelar lugar
    """
    def post(self, request, session_id, *args, **kwargs):
        member = get_active_member(request)
        if not member:
            return JsonResponse({"error": "Socio no encontrado"}, status=404)

        try:
            session = ClassSession.objects.get(id=session_id)
        except ClassSession.DoesNotExist:
            return JsonResponse({"error": "Clase no encontrada"}, status=404)

        booking = ClassBooking.objects.filter(session=session, member=member).first()
        if booking:
            booking.delete()
            return JsonResponse({
                "status": "cancelled",
                "message": f"Reserva cancelada para {session.category.name}",
                "is_booked": False
            })
        else:
            booking = ClassBooking.objects.create(
                session=session,
                member=member,
                status='RESERVADO'
            )
            return JsonResponse({
                "status": "booked",
                "message": f"Reserva confirmada para {session.category.name}",
                "is_booked": True,
                "booking_id": booking.id
            }, status=201)


class ApiSocioProfileView(View):
    """
    GET /api/v1/socio/perfil/ -> Carnet QR y membresía
    """
    def get(self, request, *args, **kwargs):
        member = get_active_member(request)
        if not member:
            return JsonResponse({"error": "Socio no encontrado"}, status=404)

        data = {
            "id": member.id,
            "name": member.full_name,
            "dni": member.dni,
            "email": member.email,
            "phone": member.phone,
            "avatar": member.avatar_url,
            "plan": {
                "name": member.plan.name if member.plan else "Sin Plan",
                "price": float(member.plan.price) if member.plan else 0.0,
                "color": member.plan.color if member.plan else "#f5b82e"
            } if member.plan else None,
            "status": member.status,
            "start_date": member.start_date.isoformat() if member.start_date else None,
            "end_date": member.end_date.isoformat() if member.end_date else None,
            "qr_code_token": f"VITALIS-MEMBER-{member.id}-{member.dni}",
            "days_remaining": (member.end_date - timezone.now().date()).days if member.end_date else 0
        }
        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
