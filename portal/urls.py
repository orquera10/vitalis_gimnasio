from django.urls import path
from .views import (
    PortalLoginView,
    PortalLogoutView,
    PortalDashboardView,
    PortalRoutineView,
    PortalProgressView,
    PortalProfileView,
    PortalAddMetricView,
    PortalBookClassToggleView
)

app_name = 'portal'

urlpatterns = [
    path('login/', PortalLoginView.as_view(), name='login'),
    path('logout/', PortalLogoutView.as_view(), name='logout'),
    path('', PortalDashboardView.as_view(), name='home'),
    path('rutina/', PortalRoutineView.as_view(), name='routine'),
    path('avances/', PortalProgressView.as_view(), name='progress'),
    path('avances/nueva/', PortalAddMetricView.as_view(), name='add_metric'),
    path('perfil/', PortalProfileView.as_view(), name='profile'),
    path('clases/<int:session_id>/toggle-reserva/', PortalBookClassToggleView.as_view(), name='book_class_toggle'),
]
