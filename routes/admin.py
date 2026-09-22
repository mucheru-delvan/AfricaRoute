from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Route, RouteStop


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 0


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "warehouse",
        "vehicle",
        "driver",
        "status",
        "scheduled_date",
        "total_distance_km",
        "estimated_duration_minutes",
    )

    list_filter = (
        "status",
        "scheduled_date",
        "warehouse",
    )

    search_fields = (
        "vehicle__registration_number",
        "driver__username",
    )

    inlines = [
        RouteStopInline,
    ]


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = (
        "route",
        "sequence",
        "order",
        "status",
        "planned_arrival_at",
        "completed_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "order__customer__name",
    )