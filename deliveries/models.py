
# Create your models here.
from django.db import models

from routes.models import RouteStop


class Delivery(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"

    class FailureReason(models.TextChoices):
        CUSTOMER_UNAVAILABLE = (
            "CUSTOMER_UNAVAILABLE",
            "Customer Unavailable",
        )
        DAMAGED_GOODS = (
            "DAMAGED_GOODS",
            "Damaged Goods",
        )
        INCORRECT_ADDRESS = (
            "INCORRECT_ADDRESS",
            "Incorrect Address",
        )
        VEHICLE_BREAKDOWN = (
            "VEHICLE_BREAKDOWN",
            "Vehicle Breakdown",
        )
        OTHER = "OTHER", "Other"

    route_stop = models.OneToOneField(
        RouteStop,
        on_delete=models.PROTECT,
        related_name="delivery",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    failure_reason = models.CharField(
        max_length=30,
        choices=FailureReason.choices,
        blank=True,
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    recipient_name = models.CharField(
        max_length=150,
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

    def __str__(self):
        return (
            f"Delivery for RouteStop "
            f"{self.route_stop_id}"
        )