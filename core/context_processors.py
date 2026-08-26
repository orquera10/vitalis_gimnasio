from datetime import timedelta
from django.utils import timezone
from django.db.models import F
from .permissions import is_admin_user, is_receptionist_user, is_trainer_user
from members.models import Member
from classes.models import ClassSession
from payments.models import Payment


def get_system_notifications(user):
    """
    Genera alertas dinámicas inteligentes en tiempo real para el centro de notificaciones:
    1. Membresías por vencer en los próximos 7 días.
    2. Membresías vencidas recientemente (últimos 3 días).
    3. Clases de hoy con cupo lleno (100% ocupadas).
    4. Pagos o cobros pendientes de registrar.
    """
    today = timezone.now().date()
    notifications = []
    
    try:
        # 1. Membresías próximas a vencer
        expiring_members = Member.objects.filter(
            status='ACTIVA',
            end_date__range=[today, today + timedelta(days=7)]
        ).select_related('plan').order_by('end_date')[:4]
        
        for m in expiring_members:
            days_left = (m.end_date - today).days
            if days_left == 0:
                time_text = "vence hoy"
            elif days_left == 1:
                time_text = "vence mañana"
            else:
                time_text = f"vence en {days_left} días"

            notifications.append({
                'id': f'exp_{m.id}',
                'icon': '⚠️',
                'title': f'Membresía por vencer: {m.full_name}',
                'description': f'Plan {m.plan.name if m.plan else "General"} ({time_text}).',
                'date_str': m.end_date.strftime('%d/%m/%Y'),
                'link': f'/miembros/{m.pk}/',
                'tag': 'Membresía',
                'tag_class': 'badge-warning'
            })

        # 2. Membresías vencidas recientemente
        recently_expired = Member.objects.filter(
            status='VENCIDO',
            end_date__range=[today - timedelta(days=3), today]
        ).select_related('plan').order_by('-end_date')[:3]
        
        for m in recently_expired:
            notifications.append({
                'id': f'venc_{m.id}',
                'icon': '🔴',
                'title': f'Socio Vencido: {m.full_name}',
                'description': f'Plan {m.plan.name if m.plan else "General"} vencido. Requiere regularización.',
                'date_str': m.end_date.strftime('%d/%m/%Y'),
                'link': f'/miembros/{m.pk}/',
                'tag': 'Vencido',
                'tag_class': 'badge-danger'
            })

        # 3. Clases de hoy con cupos llenos (100% capacidad)
        full_sessions = ClassSession.objects.filter(
            date=today,
            booked_count__gte=F('capacity')
        ).select_related('category', 'trainer')[:3]
        
        for s in full_sessions:
            notifications.append({
                'id': f'sess_{s.id}',
                'icon': '🔥',
                'title': f'Clase Llena (100% Cupo): {s.title}',
                'description': f'Horario {s.time_range} • {s.booked_count}/{s.capacity} alumnos inscriptos.',
                'date_str': 'Hoy',
                'link': f'/clases/{s.pk}/',
                'tag': 'Clase Llena',
                'tag_class': 'badge-gold'
            })

        # 4. Cobros y pagos pendientes (para admin y recepcionistas)
        if is_admin_user(user) or is_receptionist_user(user):
            pending_payments = Payment.objects.filter(status='PENDIENTE').select_related('member')[:3]
            for p in pending_payments:
                notifications.append({
                    'id': f'pay_{p.id}',
                    'icon': '💳',
                    'title': f'Pago Pendiente: {p.member.full_name}',
                    'description': f'Recibo #{p.invoice_number} por ${p.amount:,.0f} pendiente de cobro.',
                    'date_str': p.payment_date.strftime('%d/%m/%Y'),
                    'link': f'/pagos/{p.pk}/',
                    'tag': 'Cobranza',
                    'tag_class': 'badge-info'
                })
    except Exception:
        # En caso de migración o tabla no lista
        notifications = []

    return notifications


def user_roles_context(request):
    """
    Inyecta variables de permisos, roles y notificaciones del usuario en todas las plantillas.
    """
    user = request.user
    if not user.is_authenticated:
        return {
            'is_admin': False,
            'is_receptionist': False,
            'is_trainer': False,
            'can_access_reports': False,
            'can_access_settings': False,
            'can_access_payments': False,
            'can_manage_members': False,
            'can_access_classes': False,
            'current_user_role_label': 'Invitado',
            'system_notifications': [],
            'notifications_count': 0
        }

    is_admin = is_admin_user(user)
    is_receptionist = is_receptionist_user(user)
    is_trainer = is_trainer_user(user)

    # Si es staff sin grupo asignado, consideramos rol Administrador por defecto
    if not is_admin and not is_receptionist and not is_trainer:
        if user.is_staff:
            is_admin = True

    if is_admin:
        role_label = 'Administrador'
    elif is_receptionist:
        role_label = 'Recepcionista'
    elif is_trainer:
        role_label = 'Profesor / Entrenador'
    else:
        role_label = 'Personal'

    notifications = get_system_notifications(user)

    return {
        'is_admin': is_admin,
        'is_receptionist': is_receptionist,
        'is_trainer': is_trainer,
        'can_access_reports': is_admin,
        'can_access_settings': is_admin,
        'can_access_payments': is_admin or is_receptionist,
        'can_manage_members': is_admin or is_receptionist,
        'can_access_classes': is_admin or is_receptionist or is_trainer,
        'current_user_role_label': role_label,
        'system_notifications': notifications,
        'notifications_count': len(notifications)
    }
