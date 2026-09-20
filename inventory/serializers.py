from rest_framework import serializers

from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Inventory
        fields = [
            "id",
            "warehouse",
            "product",
            "quantity",
            "reserved_quantity",
            "reorder_level",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "updated_at",
        ]
