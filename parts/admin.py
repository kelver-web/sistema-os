from django.contrib import admin
from .models import Part, PartMovement


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "supplier_price", "sale_price", "location")
    search_fields = ("name", "manufacturer", "model_number")


@admin.register(PartMovement)
class PartMovementAdmin(admin.ModelAdmin):
    list_display = (
        "part",
        "movement_type",
        "quantity",
        "unit_price",
        "created_at",
    )
    list_filter = ("movement_type",)
    raw_id_fields = ("part", "service_order", "created_by")
