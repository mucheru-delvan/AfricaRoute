from django.contrib import admin

from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "warehouse",
        "product",
        "quantity",
        "reserved_quantity",
        "reorder_level",
        "updated_at",
    )

    search_fields = (
        "warehouse__name",
        "warehouse__code",
        "product__name",
        "product__sku",
    )

    list_filter = (
        "warehouse",
        "product",
    )
