from django.contrib import admin
from .models import Resource, Availability, Booking


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport_type', 'capacity', 'price_per_hour', 'is_active')
    list_filter = ('sport_type', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active', 'price_per_hour')


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('resource', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('resource', 'day_of_week')
    ordering = ('resource', 'day_of_week')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'date', 'start_time', 'end_time', 'status', 'is_recurring', 'created_at')
    list_filter = ('status', 'resource', 'date', 'is_recurring')
    search_fields = ('user__username', 'user__email', 'resource__name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)
    ordering = ('-date', 'start_time')
