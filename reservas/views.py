import calendar
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction

from .models import Resource, Booking
from .forms import BookingForm
from .utils import send_booking_confirmation, send_booking_cancellation


def _is_staff(user):
    return user.is_staff


def home(request):
    resources = Resource.objects.filter(is_active=True)
    upcoming_bookings = []
    if request.user.is_authenticated:
        upcoming_bookings = (
            request.user.bookings
            .filter(date__gte=timezone.now().date(), status=Booking.STATUS_CONFIRMED)
            .select_related('resource')
            .order_by('date', 'start_time')[:5]
        )
    return render(request, 'reservas/home.html', {
        'resources': resources,
        'upcoming_bookings': upcoming_bookings,
    })


def resource_list(request):
    sport_filter = request.GET.get('deporte', '')
    resources = Resource.objects.filter(is_active=True)
    if sport_filter:
        resources = resources.filter(sport_type=sport_filter)
    return render(request, 'reservas/resource_list.html', {
        'resources': resources,
        'sport_choices': Resource.SPORT_CHOICES,
        'sport_filter': sport_filter,
    })


def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk, is_active=True)
    availabilities = resource.availabilities.all()
    date_str = request.GET.get('fecha', '')
    selected_date = None
    booked_slots = []
    if date_str:
        try:
            selected_date = datetime.date.fromisoformat(date_str)
            booked_slots = resource.get_booked_slots(selected_date)
        except ValueError:
            selected_date = None
    return render(request, 'reservas/resource_detail.html', {
        'resource': resource,
        'availabilities': availabilities,
        'selected_date': selected_date,
        'booked_slots': booked_slots,
        'today': timezone.now().date(),
    })


def get_availability(request, resource_pk):
    date_str = request.GET.get('fecha', '')
    try:
        date = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Fecha invalida'}, status=400)
    resource = get_object_or_404(Resource, pk=resource_pk, is_active=True)
    booked = resource.get_booked_slots(date)
    return JsonResponse({
        'booked': [
            {'start': b.start_time.strftime('%H:%M'), 'end': b.end_time.strftime('%H:%M'),
             'user': b.user.get_full_name() or b.user.username}
            for b in booked
        ]
    })


@login_required
def booking_create(request, resource_pk=None):
    resource = None
    if resource_pk:
        resource = get_object_or_404(Resource, pk=resource_pk, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST, resource=resource)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            try:
                booking.full_clean()
            except Exception as e:
                messages.error(request, str(e))
                return render(request, 'reservas/booking_create.html', {'form': form, 'resource': resource})

            with transaction.atomic():
                booking.save()
                if booking.is_recurring and booking.recurrence_type == Booking.RECURRENCE_WEEKLY:
                    current_date = booking.date + datetime.timedelta(weeks=1)
                    created_count = 0
                    errors = []
                    while current_date <= booking.recurrence_end_date:
                        recurring = Booking(
                            user=request.user, resource=booking.resource,
                            date=current_date, start_time=booking.start_time,
                            end_time=booking.end_time, status=Booking.STATUS_CONFIRMED,
                            is_recurring=True, recurrence_type=booking.recurrence_type,
                            recurrence_end_date=booking.recurrence_end_date, notes=booking.notes,
                        )
                        try:
                            recurring.full_clean()
                            recurring.save()
                            created_count += 1
                        except Exception:
                            errors.append(current_date.strftime('%d/%m/%Y'))
                        current_date += datetime.timedelta(weeks=1)
                    if errors:
                        messages.warning(request, 'Algunas fechas ya estaban ocupadas: ' + ', '.join(errors))
                    messages.success(request, f'Reserva recurrente creada: {created_count + 1} reservas en total.')
                else:
                    messages.success(request, 'Reserva confirmada correctamente.')

            send_booking_confirmation(booking)
            return redirect('reservas:booking_detail', pk=booking.pk)
    else:
        initial = {'resource': resource} if resource else {}
        date_str = request.GET.get('fecha', '')
        if date_str:
            initial['date'] = date_str
        form = BookingForm(initial=initial, resource=resource)

    return render(request, 'reservas/booking_create.html', {'form': form, 'resource': resource})


@login_required
def booking_list(request):
    now = timezone.now().date()
    filter_type = request.GET.get('filter', 'upcoming')
    bookings = request.user.bookings.select_related('resource').all()

    if filter_type == 'past':
        bookings = bookings.filter(date__lt=now)
        title = 'Reservas pasadas'
    elif filter_type == 'cancelled':
        bookings = bookings.filter(status=Booking.STATUS_CANCELLED)
        title = 'Reservas canceladas'
    else:
        bookings = bookings.filter(date__gte=now).exclude(status=Booking.STATUS_CANCELLED)
        title = 'Proximas reservas'
        filter_type = 'upcoming'

    return render(request, 'reservas/booking_list.html', {
        'bookings': bookings,
        'filter_type': filter_type,
        'title': title,
    })


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'reservas/booking_detail.html', {'booking': booking})


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if not booking.can_be_cancelled:
        messages.error(request, 'Esta reserva no puede cancelarse.')
        return redirect('reservas:booking_detail', pk=pk)
    if request.method == 'POST':
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        send_booking_cancellation(booking)
        messages.success(request, 'Reserva cancelada correctamente.')
        return redirect('reservas:booking_list')
    return render(request, 'reservas/booking_cancel_confirm.html', {'booking': booking})


def calendar_view(request):
    today = timezone.now().date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if month < 1:
            month, year = 12, year - 1
        elif month > 12:
            month, year = 1, year + 1
    except (ValueError, TypeError):
        year, month = today.year, today.month

    resource_pk = request.GET.get('pista', '')
    selected_resource = None
    if resource_pk:
        selected_resource = Resource.objects.filter(pk=resource_pk, is_active=True).first()

    cal = calendar.monthcalendar(year, month)
    _, last_day = calendar.monthrange(year, month)
    month_start = datetime.date(year, month, 1)
    month_end = datetime.date(year, month, last_day)

    bookings_qs = Booking.objects.filter(
        date__range=(month_start, month_end),
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING],
    ).select_related('resource', 'user')
    if selected_resource:
        bookings_qs = bookings_qs.filter(resource=selected_resource)

    bookings_by_day = {}
    for b in bookings_qs:
        bookings_by_day.setdefault(b.date.day, []).append(b)

    weeks = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': None, 'bookings': []})
            else:
                current = datetime.date(year, month, day)
                week_data.append({
                    'day': day, 'date': current,
                    'bookings': bookings_by_day.get(day, []),
                    'is_today': current == today,
                    'is_past': current < today,
                })
        weeks.append(week_data)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render(request, 'reservas/calendar.html', {
        'weeks': weeks, 'year': year, 'month': month,
        'month_name': calendar.month_name[month],
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
        'resources': Resource.objects.filter(is_active=True),
        'selected_resource': selected_resource,
        'today': today,
        'day_names': ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'],
    })


@login_required
@user_passes_test(_is_staff, login_url='reservas:home')
def admin_panel(request):
    status_filter = request.GET.get('estado', '')
    resource_filter = request.GET.get('pista', '')
    date_filter = request.GET.get('fecha', '')

    bookings = Booking.objects.select_related('user', 'resource').all()
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if resource_filter:
        bookings = bookings.filter(resource_id=resource_filter)
    if date_filter:
        try:
            bookings = bookings.filter(date=datetime.date.fromisoformat(date_filter))
        except ValueError:
            pass

    return render(request, 'reservas/admin_panel.html', {
        'bookings': bookings.order_by('-date', 'start_time'),
        'resources': Resource.objects.filter(is_active=True),
        'status_choices': Booking.STATUS_CHOICES,
        'status_filter': status_filter,
        'resource_filter': resource_filter,
        'date_filter': date_filter,
        'total': bookings.count(),
    })


@login_required
@user_passes_test(_is_staff, login_url='reservas:home')
def admin_cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        if booking.status != Booking.STATUS_CANCELLED:
            booking.status = Booking.STATUS_CANCELLED
            booking.save()
            send_booking_cancellation(booking)
            messages.success(request, f'Reserva #{booking.pk} cancelada.')
        else:
            messages.info(request, 'La reserva ya estaba cancelada.')
    return redirect('reservas:admin_panel')
