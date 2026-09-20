from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "customer_type",
        "phone_number",
        "latitude",
        "longitude",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "phone_number",
        "email",
        "address",
    )

    list_filter = (
        "customer_type",
        "is_active",
    )