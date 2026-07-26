from django.contrib import admin
from .models import ServiceOrder, ServiceOrderItem, ServiceTimeLine

@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'client', 'equipment', 'technician', 'status', 'priority', 'opened_at'
    )
    list_filter = ('status', 'priority')
    search_fields = ('client__name', 'reported_problem')
    raw_id_fields = ('client', 'equipment', 'technician', 'opened_by')
    
    
@admin.register(ServiceOrderItem)
class ServiceOrderItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'quantity', 'unit_price', 'total', 'service_order')
    raw_id_fields = ('service_order',)
    
    
@admin.register(ServiceTimeLine)
class ServiceTimeLineAdmin(admin.ModelAdmin):
    list_display = ('action', 'service_order', 'user', 'created_at',)
    list_filter = ('action',)
    raw_id_fields = ('service_order', 'user')
    
