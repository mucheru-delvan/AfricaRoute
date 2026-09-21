from django.db import transaction
from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
        ]
        read_only_fields = [
            "id",
            "unit_price",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than zero."
            )

        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "status",
            "requested_delivery_date",
            "delivery_window_start",
            "delivery_window_end",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        start = attrs.get("delivery_window_start")
        end = attrs.get("delivery_window_end")

        if start and end and start >= end:
            raise serializers.ValidationError(
                {
                    "delivery_window_end": (
                        "Delivery window end must be later "
                        "than the start."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")

        product_ids = [item["product"].id for item in items_data]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                {
                    "items": (
                        "A product can only appear once in an order."
                    )
                }
            )

        for item_data in items_data:
            product = item_data["product"]

            if not product.is_active:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"{product.name} is not active."
                        )
                    }
                )

        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            for item_data in items_data:
                product = item_data["product"]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data["quantity"],
                    unit_price=product.unit_price,
                )

        return order
