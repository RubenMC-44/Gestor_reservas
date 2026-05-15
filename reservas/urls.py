from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    # Inicio
    path('', views.home, name='home'),

    # Pistas
    path('pistas/', views.resource_list, name='resource_list'),
    path('pistas/<int:pk>/', views.resource_detail, name='resource_detail'),
    path('pistas/<int:resource_pk>/disponibilidad/', views.get_availability, name='get_availability'),

    # Reservas
    path('reservar/', views.booking_create, name='booking_create'),
    path('reservar/<int:resource_pk>/', views.booking_create, name='booking_create_for_resource'),
    path('mis-reservas/', views.booking_list, name='booking_list'),
    path('mis-reservas/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('mis-reservas/<int:pk>/cancelar/', views.booking_cancel, name='booking_cancel'),

    # Calendario
    path('calendario/', views.calendar_view, name='calendar'),

    # Panel de administración (staff)
    path('gestion/', views.admin_panel, name='admin_panel'),
    path('gestion/<int:pk>/cancelar/', views.admin_cancel_booking, name='admin_cancel_booking'),
]
