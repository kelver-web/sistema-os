from django.contrib import admin
from .models import Client

admin.site.register(Client)


class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email", "document")
    list_filter = ("created_at",)
