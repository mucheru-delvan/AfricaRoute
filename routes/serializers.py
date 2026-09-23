from rest_framework import serializers

from orders.models import Order

from .models import Route, RouteStop


class RouteStopSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all()
    )

    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all()
    )

    class Meta:
        model = RouteStop
        fields = [
            "id",
            "route",
            "order",
            "sequence",
            "status",
            "planned_arrival_at",
            "arrived_at",
            "completed_at",
            "failure_reason",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "planned_arrival_at",
            "arrived_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate_sequence(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Sequence must be greater than zero."
            )

        return value

    def validate(self, attrs):
        route = attrs["route"]
        order = attrs["order"]

        if order.status != Order.Status.ALLOCATED:
            raise serializers.ValidationError(
                {
                    "order": (
                        "Only allocated orders can be added "
                        "to a route."
                    )
                }
            )

        if order.warehouse_id != route.warehouse_id:
            raise serializers.ValidationError(
                {
                    "order": (
                        "Order and route must use the same warehouse."
                    )
                }
            )

        return attrs


class RouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            "id",
            "warehouse",
            "vehicle",
            "driver",
            "status",
            "scheduled_date",
            "total_distance_km",
            "estimated_duration_minutes",
            "optimized_at",
            "started_at",
            "completed_at",
            "stops",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "total_distance_km",
            "estimated_duration_minutes",
            "optimized_at",
            "started_at",
            "completed_at",
            "stops",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        vehicle = attrs.get("vehicle")
        driver = attrs.get("driver")

        if vehicle and not vehicle.is_active:
            raise serializers.ValidationError(
                {"vehicle": "Vehicle is not active."}
            )

        if driver and not driver.is_active:
            raise serializers.ValidationError(
                {"driver": "Driver is not active."}
            )

        return attrs