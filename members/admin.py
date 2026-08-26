from django.contrib import admin
from .models import Plan, Member


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'color', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'dni', 'email', 'phone', 'plan', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'plan', 'gender')
    search_fields = ('first_name', 'last_name', 'dni', 'email', 'phone')
    date_hierarchy = 'start_date'
    ordering = ('-created_at',)
