from django.db import models

# Create your models here.
from django.db import models


class Vehicle(models.Model):

    class VehicleType(models.TextChoices):
        TRUCK = "TRUCK", "Truck"
        VAN = "VAN", "Van"
        MOTORCYCLE = "MOTORCYCLE", "Motorcycle"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        INACTIVE = "INACTIVE", "Inactive"

    registration_number = models.CharField(
        max_length=20,
        unique=True,
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
    )

    capacity = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration_number} ({self.vehicle_type})"