from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'member', 'plan', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date', 'plan')
    search_fields = ('invoice_number', 'member__first_name', 'member__last_name', 'member__dni', 'notes')
    date_hierarchy = 'payment_date'
