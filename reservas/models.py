from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


class Resource(models.Model):
    SPORT_CHOICES = [
        ('padel', 'Pádel'),
        ('tenis', 'Tenis'),
        ('futbol_sala', 'Fútbol Sala'),
        ('badminton', 'Bádminton'),
        ('squash', 'Squash'),
        ('baloncesto', 'Baloncesto'),
        ('otro', 'Otro'),
    ]

    name = models.CharField('nombre', max_length=100)
    sport_type = models.CharField('deporte', max_length=20, choices=SPORT_CHOICES)
    description = models.TextField('descripción', blank=True)
    capacity = models.PositiveIntegerField('capacidad (jugadores)', default=2)
    price_per_hour = models.DecimalField('precio por hora (€)', max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField('activa', default=True)
    image = models.ImageField('imagen', upload_to='resources/', blank=True, null=True)

    class Meta:
        verbose_name = 'Pista'
        verbose_name_plural = 'Pistas'
        ordering = ['sport_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_sport_type_display()})"

    def get_booked_slots(self, date):
        """Devuelve los tramos reservados (confirmados o pendientes) para una fecha."""
        return self.bookings.filter(
            date=date,
            status__in=['confirmed', 'pending'],
        ).order_by('start_time')


class Availability(models.Model):
    DAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE,
        related_name='availabilities', verbose_name='pista'
    )
    day_of_week = models.IntegerField('día de la semana', choices=DAY_CHOICES)
    start_time = models.TimeField('hora apertura')
    end_time = models.TimeField('hora cierre')

    class Meta:
        verbose_name = 'Disponibilidad'
        verbose_name_plural = 'Disponibilidades'
        unique_together = ('resource', 'day_of_week')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.resource.name} — {self.get_day_of_week_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('La hora de apertura debe ser anterior a la hora de cierre.')


class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_CONFIRMED, 'Confirmada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    RECURRENCE_NONE = 'none'
    RECURRENCE_WEEKLY = 'weekly'

    RECURRENCE_CHOICES = [
        (RECURRENCE_NONE, 'Sin repetición'),
        (RECURRENCE_WEEKLY, 'Semanal'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='bookings', verbose_name='usuario'
    )
    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE,
        related_name='bookings', verbose_name='pista'
    )
    date = models.DateField('fecha')
    start_time = models.TimeField('hora inicio')
    end_time = models.TimeField('hora fin')
    status = models.CharField(
        'estado', max_length=20,
        choices=STATUS_CHOICES, default=STATUS_CONFIRMED
    )
    is_recurring = models.BooleanField('es recurrente', default=False)
    recurrence_type = models.CharField(
        'tipo de recurrencia', max_length=20,
        choices=RECURRENCE_CHOICES, default=RECURRENCE_NONE
    )
    recurrence_end_date = models.DateField('fin de recurrencia', null=True, blank=True)
    notes = models.TextField('notas', blank=True)
    created_at = models.DateTimeField('creado el', auto_now_add=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f"{self.user.username} — {self.resource.name} — {self.date} {self.start_time:%H:%M}"

    def clean(self):
        if not self.start_time or not self.end_time or not self.date or not self.resource_id:
            return

        if self.start_time >= self.end_time:
            raise ValidationError('La hora de inicio debe ser anterior a la hora de fin.')

        if self.date < timezone.now().date():
            raise ValidationError('No puedes hacer reservas en fechas pasadas.')

        # Comprueba solapamiento con otras reservas activas
        overlapping = Booking.objects.filter(
            resource=self.resource,
            date=self.date,
            status__in=[self.STATUS_CONFIRMED, self.STATUS_PENDING],
        ).exclude(pk=self.pk).filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )

        if overlapping.exists():
            raise ValidationError(
                'Ya existe una reserva para este horario en la pista seleccionada. '
                'Por favor elige otro tramo horario.'
            )

    @property
    def duration_hours(self):
        """Duración de la reserva en horas (float)."""
        start = datetime.datetime.combine(self.date, self.start_time)
        end = datetime.datetime.combine(self.date, self.end_time)
        return (end - start).seconds / 3600

    @property
    def total_price(self):
        from decimal import Decimal
        return self.resource.price_per_hour * Decimal(str(self.duration_hours))

    @property
    def is_upcoming(self):
        return self.date >= timezone.now().date() and self.status != self.STATUS_CANCELLED

    @property
    def can_be_cancelled(self):
        return self.status != self.STATUS_CANCELLED and self.date >= timezone.now().date()
