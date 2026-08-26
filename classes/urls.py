from django.urls import path
from .views import (
    ClassCalendarView,
    ClassScheduleCreateView,
    ClassSessionCreateView,
    ClassDetailView,
    ClassSessionDeleteView,
    ClassBookingCreateView,
    ClassBookingStatusUpdateView,
    ClassBookingDeleteView,
    TrainerListView,
    TrainerCreateView,
    TrainerDetailView,
    TrainerUpdateView,
    TrainerDeleteView
)

app_name = 'classes'

urlpatterns = [
    # Clases & Calendario
    path('', ClassCalendarView.as_view(), name='calendar'),
    path('programar-horario/', ClassScheduleCreateView.as_view(), name='schedule_create'),
    path('agendar-sesion/', ClassSessionCreateView.as_view(), name='session_create'),
    path('sesion/<int:pk>/', ClassDetailView.as_view(), name='detail'),
    path('sesion/<int:pk>/inscribir/', ClassBookingCreateView.as_view(), name='booking_create'),
    path('reserva/<int:pk>/estado/', ClassBookingStatusUpdateView.as_view(), name='booking_status_update'),
    path('reserva/<int:pk>/cancelar/', ClassBookingDeleteView.as_view(), name='booking_delete'),
    path('sesion/<int:pk>/cancelar/', ClassSessionDeleteView.as_view(), name='delete'),

    # Entrenadores / Instructores
    path('entrenadores/', TrainerListView.as_view(), name='trainer_list'),
    path('entrenadores/nuevo/', TrainerCreateView.as_view(), name='trainer_create'),
    path('entrenadores/<int:pk>/', TrainerDetailView.as_view(), name='trainer_detail'),
    path('entrenadores/<int:pk>/editar/', TrainerUpdateView.as_view(), name='trainer_update'),
    path('entrenadores/<int:pk>/eliminar/', TrainerDeleteView.as_view(), name='trainer_delete'),
]
