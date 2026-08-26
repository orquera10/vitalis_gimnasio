from django.urls import path
from .views import (
    PaymentListView,
    PaymentCreateView,
    PaymentDetailView,
    PaymentCancelView
)

app_name = 'payments'

urlpatterns = [
    path('', PaymentListView.as_view(), name='list'),
    path('nuevo/', PaymentCreateView.as_view(), name='create'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='detail'),
    path('<int:pk>/anular/', PaymentCancelView.as_view(), name='cancel'),
]
