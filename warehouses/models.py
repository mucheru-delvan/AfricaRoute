from django.db import models

# Create your models here.

class Warehouse(models.Model):
    name = models.CharField(max_length=100)

    code = models.CharField(
        max_length=20,
        unique=True,
    )

    location = models.CharField(max_length=100)

    address = models.TextField(blank=True)

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
        return f"{self.name} ({self.code})"