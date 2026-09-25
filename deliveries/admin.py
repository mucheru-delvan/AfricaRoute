from django.contrib import admin

# Register your models here.
from .models import Delivery


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "route_stop",
        "status",
        "recipient_name",
        "delivered_at",
        "failed_at",
    )

    list_filter = (
        "status",
        "failure_reason",
    )

    search_fields = (
        "recipient_name",
        "route_stop__order__customer__name",
    )