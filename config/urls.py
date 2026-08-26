from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from members.views import KioskTerminalView, KioskCheckInAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('terminal/', KioskTerminalView.as_view(), name='kiosk_terminal_root'),
    path('terminal/checkin/', KioskCheckInAPIView.as_view(), name='kiosk_checkin_root'),
    path('socio/', include('portal.urls')),
    path('api/v1/', include('api.urls')),
    path('miembros/', include('members.urls')),
    path('clases/', include('classes.urls')),
    path('pagos/', include('payments.urls')),
    path('reportes/', include('reports.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
