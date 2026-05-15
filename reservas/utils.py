from django.core.mail import send_mail
from django.conf import settings


def send_booking_confirmation(booking):
    """Envía un email de confirmación al usuario cuando se crea una reserva."""
    subject = f'Reserva confirmada — {booking.resource.name} el {booking.date:%d/%m/%Y}'
    message = (
        f'Hola {booking.user.first_name or booking.user.username},\n\n'
        f'Tu reserva ha sido confirmada con los siguientes detalles:\n\n'
        f'  Pista:      {booking.resource.name} ({booking.resource.get_sport_type_display()})\n'
        f'  Fecha:      {booking.date:%d/%m/%Y}\n'
        f'  Horario:    {booking.start_time:%H:%M} – {booking.end_time:%H:%M}\n'
        f'  Duración:   {booking.duration_hours:.1f} hora(s)\n'
        f'  Precio:     {booking.total_price:.2f} €\n'
    )
    if booking.is_recurring:
        message += f'  Recurrencia: semanal hasta el {booking.recurrence_end_date:%d/%m/%Y}\n'
    if booking.notes:
        message += f'  Notas:      {booking.notes}\n'

    message += '\nGracias por usar GestorReservas. ¡Que disfrutes del partido!'

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        fail_silently=True,
    )


def send_booking_cancellation(booking):
    """Envía un email de cancelación al usuario."""
    subject = f'Reserva cancelada — {booking.resource.name} el {booking.date:%d/%m/%Y}'
    message = (
        f'Hola {booking.user.first_name or booking.user.username},\n\n'
        f'Tu reserva ha sido cancelada:\n\n'
        f'  Pista:   {booking.resource.name}\n'
        f'  Fecha:   {booking.date:%d/%m/%Y}\n'
        f'  Horario: {booking.start_time:%H:%M} – {booking.end_time:%H:%M}\n\n'
        f'Si no fuiste tú quien la canceló o tienes alguna duda, contacta con nosotros.\n\n'
        f'Un saludo,\nEl equipo de GestorReservas'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        fail_silently=True,
    )
