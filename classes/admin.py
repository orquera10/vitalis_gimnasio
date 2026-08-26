from django.contrib import admin
from .models import Trainer, ClassCategory, ClassSchedule, ClassSession, ClassBooking


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialty', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('first_name', 'last_name', 'specialty')


@admin.register(ClassCategory)
class ClassCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'icon')
    search_fields = ('name',)


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'trainer', 'day_of_week', 'start_time', 'end_time', 'room', 'capacity', 'is_active')
    list_filter = ('day_of_week', 'category', 'trainer', 'is_active')
    search_fields = ('title', 'room')


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'trainer', 'date', 'start_time', 'end_time', 'booked_count', 'capacity', 'status')
    list_filter = ('status', 'category', 'trainer', 'date')
    search_fields = ('title', 'room')
    date_hierarchy = 'date'


@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ('member', 'session', 'status', 'booking_date')
    list_filter = ('status', 'booking_date', 'session__category')
    search_fields = ('member__first_name', 'member__last_name', 'member__dni', 'session__title')
