

# Register your models here.
from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "status",
        "requested_delivery_date",
        "created_at",
    )

    search_fields = (
        "customer__name",
    )

    list_filter = (
        "status",
        "requested_delivery_date",
    )

    inlines = [
        OrderItemInline,
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price",
    )

    search_fields = (
        "order__customer__name",
        "product__name",
        "product__sku",
    )