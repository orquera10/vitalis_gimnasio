from django.urls import path
from .views import (
    ApiSocioDashboardView,
    ApiSocioRoutineView,
    ApiSocioProgressView,
    ApiSocioClassBookingView,
    ApiSocioProfileView
)

app_name = 'api'

urlpatterns = [
    path('socio/dashboard/', ApiSocioDashboardView.as_view(), name='socio_dashboard'),
    path('socio/rutina/', ApiSocioRoutineView.as_view(), name='socio_routine'),
    path('socio/avances/', ApiSocioProgressView.as_view(), name='socio_progress'),
    path('socio/clases/<int:session_id>/reservar/', ApiSocioClassBookingView.as_view(), name='socio_class_booking'),
    path('socio/perfil/', ApiSocioProfileView.as_view(), name='socio_profile'),
]
