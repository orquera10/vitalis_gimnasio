from django import forms
from .models import BodyMetric


class BodyMetricForm(forms.ModelForm):
    class Meta:
        model = BodyMetric
        fields = ['date', 'weight_kg', 'body_fat_pct', 'muscle_mass_kg', 'waist_cm', 'chest_cm', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control-dark'}),
            'weight_kg': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'Ej. 78.5', 'class': 'form-control-dark'}),
            'body_fat_pct': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'Ej. 18.2', 'class': 'form-control-dark'}),
            'muscle_mass_kg': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'Ej. 42.1', 'class': 'form-control-dark'}),
            'waist_cm': forms.NumberInput(attrs={'step': '0.5', 'placeholder': 'Ej. 86.0', 'class': 'form-control-dark'}),
            'chest_cm': forms.NumberInput(attrs={'step': '0.5', 'placeholder': 'Ej. 102.0', 'class': 'form-control-dark'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Notas sobre tu estado físico...', 'class': 'form-control-dark'}),
        }


class PortalLoginForm(forms.Form):
    username_or_dni = forms.CharField(
        label="DNI o Usuario",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ingresa tu DNI (ej: 38492019)',
            'class': 'portal-form-control',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Tu contraseña de socio',
            'class': 'portal-form-control',
            'autocomplete': 'current-password'
        })
    )
