from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from .models import Booking, Resource, Availability


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['resource', 'date', 'start_time', 'end_time', 'is_recurring',
                  'recurrence_type', 'recurrence_end_date', 'notes']
        widgets = {
            'resource': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_recurring'}),
            'recurrence_type': forms.Select(attrs={'class': 'form-select'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                           'placeholder': 'Anotaciones opcionales...'}),
        }
        labels = {
            'resource': 'Pista',
            'date': 'Fecha',
            'start_time': 'Hora de inicio',
            'end_time': 'Hora de fin',
            'is_recurring': '¿Reserva recurrente?',
            'recurrence_type': 'Frecuencia',
            'recurrence_end_date': 'Repetir hasta',
            'notes': 'Notas',
        }

    def __init__(self, *args, resource=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo pistas activas
        self.fields['resource'].queryset = Resource.objects.filter(is_active=True)
        # Preseleccionar pista si viene del contexto
        if resource:
            self.fields['resource'].initial = resource

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        resource = cleaned_data.get('resource')
        is_recurring = cleaned_data.get('is_recurring')
        recurrence_type = cleaned_data.get('recurrence_type')
        recurrence_end_date = cleaned_data.get('recurrence_end_date')

        if date and date < timezone.now().date():
            self.add_error('date', 'No puedes reservar en fechas pasadas.')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'La hora de fin debe ser posterior a la hora de inicio.')

        if is_recurring:
            if not recurrence_type or recurrence_type == Booking.RECURRENCE_NONE:
                self.add_error('recurrence_type', 'Selecciona la frecuencia de repetición.')
            if not recurrence_end_date:
                self.add_error('recurrence_end_date', 'Indica hasta qué fecha se repetirá la reserva.')
            elif date and recurrence_end_date <= date:
                self.add_error('recurrence_end_date', 'La fecha de fin debe ser posterior a la fecha de inicio.')

        return cleaned_data


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['resource', 'day_of_week', 'start_time', 'end_time']
        widgets = {
            'resource': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
