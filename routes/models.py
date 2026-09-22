from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models

from orders.models import Order
from warehouses.models import Warehouse
from fleet.models import Vehicle


class Route(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPTIMIZED = "OPTIMIZED", "Optimized"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="routes",
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="routes",
        null=True,
        blank=True,
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="routes",
        null=True,
        blank=True,
        limit_choices_to={"role": "DRIVER"},
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    scheduled_date = models.DateField()

    total_distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    estimated_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    optimized_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Route #{self.id} - {self.scheduled_date}"


class RouteStop(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ARRIVED = "ARRIVED", "Arrived"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="stops",
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="route_stops",
    )

    sequence = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    planned_arrival_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    arrived_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failure_reason = models.CharField(
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["route", "sequence"],
                name="unique_route_stop_sequence",
            ),
            models.UniqueConstraint(
                fields=["route", "order"],
                name="unique_order_per_route",
            ),
        ]

    def __str__(self):
        return f"Route #{self.route_id} - Stop {self.sequence}"