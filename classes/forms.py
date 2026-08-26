from django import forms
from members.models import Member
from .models import ClassSchedule, ClassSession, Trainer, ClassCategory, ClassBooking


class ClassScheduleForm(forms.ModelForm):
    """
    Formulario para configurar horarios recurrentes (ej. Miércoles y Viernes 20:00 a 22:00).
    """
    DAYS_CHOICES = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]

    selected_days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'day-checkbox'}),
        required=True,
        label="Días en que se imparte la clase"
    )

    class Meta:
        model = ClassSchedule
        fields = ['title', 'category', 'trainer', 'start_time', 'end_time', 'room', 'capacity', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Entrenamiento Funcional'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'value': '20:00'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'value': '22:00'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Box Funcional / Sala 1'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '20'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClassSessionForm(forms.ModelForm):
    """
    Formulario para programar o editar una sesión de clase puntual en el calendario.
    """
    class Meta:
        model = ClassSession
        fields = ['title', 'category', 'trainer', 'date', 'start_time', 'end_time', 'room', 'capacity', 'booked_count', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Crossfit WOD'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sala Principal'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'booked_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        plan_name = obj.plan.name if obj.plan else "Sin Plan"
        return f"{obj.full_name} | DNI: {obj.dni} | Plan: {plan_name}"


class ClassBookingForm(forms.ModelForm):
    """
    Formulario para inscribir un socio a una sesión puntual de clase.
    """
    member = MemberChoiceField(
        queryset=Member.objects.filter(status='ACTIVA').select_related('plan').order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'member-select'}),
        label="Seleccionar Socio Activo",
        empty_label="-- Busca y selecciona un socio activo --"
    )

    class Meta:
        model = ClassBooking
        fields = ['member', 'notes']
        widgets = {
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observaciones opcionales (ej. primera clase, lesión leve)'}),
        }


class TrainerForm(forms.ModelForm):
    """
    Formulario para registrar o editar un entrenador / instructor.
    """
    class Meta:
        model = Trainer
        fields = ['first_name', 'last_name', 'specialty', 'email', 'phone', 'avatar_file', 'avatar', 'bio', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Funcional, Crossfit, Yoga'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@vitalisfitness.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'avatar_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'avatar-file-input'}),
            'avatar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'O pega una URL de imagen externa...', 'id': 'avatar-url-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Biografía, certificaciones, experiencia deportiva...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
