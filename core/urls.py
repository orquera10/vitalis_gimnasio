from django.urls import path
from .views import CustomLoginView, CustomLogoutView, HomeView
from .views_settings import (
    SettingsView,
    PlanCreateModalView,
    PlanUpdateModalView,
    PlanDeleteModalView,
    CategoryCreateModalView,
    CategoryUpdateModalView,
    CategoryDeleteModalView,
    BackupExportJSONView,
    UserCreateModalView,
    UserToggleStatusModalView,
    UserDeleteModalView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Centro de Configuración & Ajustes
    path('configuracion/', SettingsView.as_view(), name='settings'),
    path('configuracion/planes/nuevo/', PlanCreateModalView.as_view(), name='plan_create'),
    path('configuracion/planes/<int:pk>/editar/', PlanUpdateModalView.as_view(), name='plan_update'),
    path('configuracion/planes/<int:pk>/eliminar/', PlanDeleteModalView.as_view(), name='plan_delete'),
    path('configuracion/disciplinas/nueva/', CategoryCreateModalView.as_view(), name='category_create'),
    path('configuracion/disciplinas/<int:pk>/editar/', CategoryUpdateModalView.as_view(), name='category_update'),
    path('configuracion/disciplinas/<int:pk>/eliminar/', CategoryDeleteModalView.as_view(), name='category_delete'),
    path('configuracion/backup/', BackupExportJSONView.as_view(), name='backup'),
    
    # Gestión de Usuarios & Roles de Empleados
    path('configuracion/usuarios/nuevo/', UserCreateModalView.as_view(), name='user_create'),
    path('configuracion/usuarios/<int:pk>/toggle/', UserToggleStatusModalView.as_view(), name='user_toggle'),
    path('configuracion/usuarios/<int:pk>/eliminar/', UserDeleteModalView.as_view(), name='user_delete'),
]
