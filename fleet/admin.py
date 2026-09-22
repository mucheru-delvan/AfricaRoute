from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "vehicle_type",
        "capacity",
        "status",
        "is_active",
        "created_at",
    )

    search_fields = (
        "registration_number",
    )

    list_filter = (
        "vehicle_type",
        "status",
        "is_active",
    )