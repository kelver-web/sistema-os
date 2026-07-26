from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'category', 'client', 'serial_number')
    list_filter = ('category', 'client')
    search_fields = ('brand', 'model', 'serial_number')
