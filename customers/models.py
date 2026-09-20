
from django.db import models


class Customer(models.Model):

    class CustomerType(models.TextChoices):
        KIOSK = "KIOSK", "Kiosk"
        SUPERMARKET = "SUPERMARKET", "Supermarket"
        RESTAURANT = "RESTAURANT", "Restaurant"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"

    name = models.CharField(max_length=150)

    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
    )

    phone_number = models.CharField(max_length=20)

    email = models.EmailField(blank=True)

    address = models.TextField()

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.customer_type})"