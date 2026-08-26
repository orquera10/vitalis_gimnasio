from django import forms
from .models import Member, Plan


class MemberForm(forms.ModelForm):
    """
    Formulario estilizado para la creación y edición de socios/miembros.
    """
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'dni', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'avatar_file', 'avatar',
            'plan', 'status', 'start_date', 'end_date',
            'emergency_contact_name', 'emergency_contact_phone', 'medical_notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sofía'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Rodriguez'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 12.345.678-9'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'sofia@ejemplo.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Av. Libertador 1234'}),
            'avatar_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'avatar-file-input'}),
            'avatar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'O pega una URL de imagen externa...', 'id': 'avatar-url-input'}),
            'plan': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de familiar o contacto'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de urgencia'}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Alergias, lesiones previas, aptitud física...'}),
        }


class PlanForm(forms.ModelForm):
    """
    Formulario para gestionar tipos de planes de membresía.
    """
    class Meta:
        model = Plan
        fields = ['name', 'price', 'duration_days', 'color', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Black Pass VIP'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '45000'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#f5b82e'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Acceso total a todas las sedes y clases'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
