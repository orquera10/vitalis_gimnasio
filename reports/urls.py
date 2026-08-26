from django.urls import path
from .views import (
    ReportsDashboardView,
    ExportPaymentsCSVView,
    ExportMembersCSVView,
    ExportAttendanceCSVView,
    PrintableExecutiveReportView
)

app_name = 'reports'

urlpatterns = [
    path('', ReportsDashboardView.as_view(), name='dashboard'),
    path('imprimir/', PrintableExecutiveReportView.as_view(), name='printable'),
    path('exportar/pagos/', ExportPaymentsCSVView.as_view(), name='export_payments_csv'),
    path('exportar/socios/', ExportMembersCSVView.as_view(), name='export_members_csv'),
    path('exportar/asistencias/', ExportAttendanceCSVView.as_view(), name='export_attendance_csv'),
]
