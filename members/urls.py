from django.urls import path
from .views import (
    MemberListView,
    MemberDetailView,
    MemberCreateView,
    MemberUpdateView,
    MemberDeleteView,
    MemberPortalResetPasswordView,
    KioskTerminalView,
    KioskCheckInAPIView
)

app_name = 'members'

urlpatterns = [
    path('', MemberListView.as_view(), name='list'),
    path('nuevo/', MemberCreateView.as_view(), name='create'),
    path('terminal/', KioskTerminalView.as_view(), name='terminal'),
    path('terminal/checkin/', KioskCheckInAPIView.as_view(), name='terminal_checkin'),
    path('<int:pk>/', MemberDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', MemberUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', MemberDeleteView.as_view(), name='delete'),
    path('<int:pk>/reset-portal/', MemberPortalResetPasswordView.as_view(), name='reset_portal_password'),
]
