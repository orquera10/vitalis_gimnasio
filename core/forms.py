from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import GymSetting
from members.models import Plan
from classes.models import ClassCategory


class CustomLoginForm(AuthenticationForm):
    """
    Formulario de autenticación personalizado con clases CSS y estilos
    adaptados al diseño del gimnasio.
    """
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tu usuario',
                'autocomplete': 'username',
                'autofocus': True,
                'id': 'id_username',
            }
        )
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
                'id': 'id_password',
            }
        )
    )


class GymSettingForm(forms.ModelForm):
    """
    Formulario de edición de perfil, facturación y reglas operativas del gimnasio.
    """
    class Meta:
        model = GymSetting
        fields = [
            'gym_name', 'branch_name', 'tax_id', 'address',
            'phone', 'whatsapp', 'email', 'bank_cbu',
            'bank_alias', 'receipt_footer', 'days_advance_notice',
            'grace_period_days', 'default_class_capacity'
        ]
        widgets = {
            'gym_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Vitalis Fitness Club'}),
            'branch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sede Central • Palermo'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 30-71829304-5'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Av. del Libertador 4500'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +54 11 4899-2030'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +54 9 11 5500-8822'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contacto@vitalisfitness.com'}),
            'bank_cbu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000003100045678912345'}),
            'bank_alias': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VITALIS.FITNESS.PAGO'}),
            'receipt_footer': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Mensaje al pie del comprobante...'}),
            'days_advance_notice': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60}),
            'grace_period_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 30}),
            'default_class_capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        }


class PlanModalForm(forms.ModelForm):
    """
    Formulario para crear o editar planes de membresía.
    """
    class Meta:
        model = Plan
        fields = ['name', 'price', 'duration_days', 'color', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Black Pass VIP'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '65000.00', 'step': '500'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Acceso total a musculación, clases y spa...'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'width: 18px; height: 18px; accent-color: var(--gold-primary); cursor: pointer;'}),
        }


class CategoryModalForm(forms.ModelForm):
    """
    Formulario para crear o editar disciplinas deportivas.
    """
    class Meta:
        model = ClassCategory
        fields = ['name', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Spinning Pro / HIIT'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la disciplina...'}),
        }
