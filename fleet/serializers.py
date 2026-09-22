from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "registration_number",
            "vehicle_type",
            "capacity",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Vehicle capacity must be greater than zero."
            )

        return value
