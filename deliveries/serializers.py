from rest_framework import serializers

from .models import Delivery


class DeliverySerializer(serializers.ModelSerializer):

    class Meta:
        model = Delivery
        fields = [
            "id",
            "route_stop",
            "status",
            "failure_reason",
            "delivered_at",
            "failed_at",
            "recipient_name",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "delivered_at",
            "failed_at",
            "created_at",
            "updated_at",
        ]
