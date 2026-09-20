from rest_framework import serializers

from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "code",
            "location",
            "address",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]
