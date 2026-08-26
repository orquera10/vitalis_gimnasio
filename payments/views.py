from core.permissions import PaymentsAccessRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal
from members.models import Member, Plan
from .models import Payment
from .forms import PaymentForm


class PaymentListView(PaymentsAccessRequiredMixin, ListView):
    """
    Panel financiero y listado de transacciones de pagos.
    """
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.select_related('member', 'plan').order_by('-payment_date', '-created_at')

        # 1. Búsqueda por texto (Nombre, DNI, Recibo, Notas)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(invoice_number__icontains=q) |
                Q(member__first_name__icontains=q) |
                Q(member__last_name__icontains=q) |
                Q(member__dni__icontains=q) |
                Q(notes__icontains=q)
            )

        # 2. Filtro por Método de Pago
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(payment_method=method)

        # 3. Filtro por Estado
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # 4. Filtro por Rango de Fechas
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month

        # Pagos completados este mes
        month_payments = Payment.objects.filter(
            payment_date__year=current_year,
            payment_date__month=current_month
        )

        month_completed = month_payments.filter(status='COMPLETADO')
        monthly_income = month_completed.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        monthly_avg = month_completed.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
        pending_count = month_payments.filter(status='PENDIENTE').count()

        # Métricas Globales
        context['kpis'] = {
            'monthly_income': monthly_income,
            'monthly_completed_count': month_completed.count(),
            'monthly_avg': monthly_avg,
            'pending_count': pending_count,
            'total_all_time': Payment.objects.filter(status='COMPLETADO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        }

        # Opciones de filtros
        context['current_q'] = self.request.GET.get('q', '')
        context['current_method'] = self.request.GET.get('method', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['methods'] = Payment.METHOD_CHOICES
        context['statuses'] = Payment.STATUS_CHOICES

        return context


class PaymentCreateView(PaymentsAccessRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Registrar un nuevo cobro o pago de cuota.
    """
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    success_message = "¡Pago registrado exitosamente! Comprobante emitido."

    def get_initial(self):
        initial = super().get_initial()
        member_id = self.request.GET.get('member')
        if member_id:
            try:
                member = Member.objects.get(pk=member_id)
                initial['member'] = member
                if member.plan:
                    initial['plan'] = member.plan
                    initial['amount'] = member.plan.price
            except Member.DoesNotExist:
                pass
        return initial

    def get_success_url(self):
        return reverse_lazy('payments:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans_json'] = {p.id: float(p.price) for p in Plan.objects.all()}
        return context


class PaymentDetailView(PaymentsAccessRequiredMixin, DetailView):
    """
    Ficha de comprobante / recibo digital oficial con opción de impresión.
    """
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'


class PaymentCancelView(PaymentsAccessRequiredMixin, View):
    """
    Anular o reembolsar un pago.
    """
    def post(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, pk=pk)
        payment.status = 'ANULADO'
        payment.save(update_fields=['status'])
        messages.warning(request, f"El comprobante {payment.invoice_number} por ${payment.amount:,.0f} ha sido marcado como ANULADO.")
        return redirect('payments:detail', pk=payment.pk)
