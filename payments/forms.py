from django import forms
from django.utils import timezone
from members.models import Member, Plan
from .models import Payment


class MemberPaymentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        plan_name = obj.plan.name if obj.plan else "Sin Plan"
        return f"{obj.full_name} | DNI: {obj.dni} | Plan: {plan_name} ({obj.get_status_display()})"


class PaymentForm(forms.ModelForm):
    """
    Formulario para registrar un pago o cobro de cuota.
    """
    member = MemberPaymentChoiceField(
        queryset=Member.objects.select_related('plan').order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'payment-member-select'}),
        label="Socio / Cliente *",
        empty_label="-- Selecciona un socio registrado --"
    )

    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True).order_by('-price'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'payment-plan-select'}),
        label="Plan / Concepto de Membresía",
        empty_label="-- Selecciona el plan abonado (o deja vacío si es otro concepto) --"
    )

    class Meta:
        model = Payment
        fields = [
            'member', 'plan', 'amount', 'payment_method',
            'status', 'payment_date', 'invoice_number',
            'notes', 'auto_renew_membership'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 45000', 'step': '0.01', 'id': 'payment-amount-input'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Autogenerado si se deja vacío (ej. REC-2026-0001)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'N° de transferencia, código de autorización o notas adicionales...'}),
            'auto_renew_membership': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
