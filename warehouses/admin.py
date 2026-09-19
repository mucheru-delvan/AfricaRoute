from django.contrib import admin

from .models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "location",
        "latitude",
        "longitude",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
        "location",
    )

    list_filter = (
        "is_active",
    )
