from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from fleet.models import Vehicle
from inventory.models import Inventory
from routes.models import Route, RouteStop

from .models import Delivery


@transaction.atomic
def start_delivery(delivery_id):
    delivery = (
        Delivery.objects
        .select_for_update()
        .get(pk=delivery_id)
    )

    route_stop = (
        RouteStop.objects
        .select_for_update()
        .select_related("route")
        .get(pk=delivery.route_stop_id)
    )

    route = (
        Route.objects
        .select_for_update()
        .get(pk=route_stop.route_id)
    )

    if route.status != Route.Status.IN_PROGRESS:
        raise ValidationError(
            f"Only in-progress routes can start deliveries. "
            f"Current status: {route.status}."
        )

    if delivery.status != Delivery.Status.PENDING:
        raise ValidationError(
            f"Only pending deliveries can be started. "
            f"Current status: {delivery.status}."
        )

    if route_stop.status != RouteStop.Status.PENDING:
        raise ValidationError(
            f"Route stop is not pending. "
            f"Current status: {route_stop.status}."
        )

    delivery.status = Delivery.Status.IN_PROGRESS

    delivery.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    route_stop.status = RouteStop.Status.ARRIVED
    route_stop.arrived_at = timezone.now()

    route_stop.save(
        update_fields=[
            "status",
            "arrived_at",
            "updated_at",
        ]
    )

    return delivery


@transaction.atomic
def complete_delivery(delivery_id):
    delivery = (
        Delivery.objects
        .select_for_update()
        .get(pk=delivery_id)
    )

    route_stop = (
        RouteStop.objects
        .select_for_update()
        .get(pk=delivery.route_stop_id)
    )

    route = (
        Route.objects
        .select_for_update()
        .get(pk=route_stop.route_id)
    )

    if delivery.status != Delivery.Status.IN_PROGRESS:
        raise ValidationError(
            f"Only in-progress deliveries can be completed. "
            f"Current status: {delivery.status}."
        )

    if route_stop.status != RouteStop.Status.ARRIVED:
        raise ValidationError(
            f"Route stop must be marked as arrived before completion. "
            f"Current status: {route_stop.status}."
        )

    order = (
        route_stop.order
    )

    if order.status != "ALLOCATED":
        raise ValidationError(
            f"Order {order.id} is not allocated. "
            f"Current status: {order.status}."
        )

    if order.warehouse_id != route.warehouse_id:
        raise ValidationError(
            f"Order {order.id} belongs to a different warehouse."
        )

    items = list(
        order.items.all()
    )

    if not items:
        raise ValidationError(
            f"Order {order.id} has no items."
        )

    # Lock all inventory records for this order's warehouse.
    inventory_records = (
        Inventory.objects
        .select_for_update()
        .filter(
            warehouse_id=order.warehouse_id,
            product_id__in=[
                item.product_id
                for item in items
            ],
        )
    )

    inventory_by_product = {
        inventory.product_id: inventory
        for inventory in inventory_records
    }

    for item in items:
        inventory = inventory_by_product.get(
            item.product_id
        )

        if inventory is None:
            raise ValidationError(
                f"No inventory exists for product "
                f"{item.product_id}."
            )

        if inventory.reserved_quantity < item.quantity:
            raise ValidationError(
                f"Reserved quantity for product "
                f"{item.product_id} is insufficient."
            )

        if inventory.quantity < item.quantity:
            raise ValidationError(
                f"Physical quantity for product "
                f"{item.product_id} is insufficient."
            )

    # Convert the reservation into an actual stock deduction.
    for item in items:
        inventory = inventory_by_product[item.product_id]

        inventory.quantity -= item.quantity
        inventory.reserved_quantity -= item.quantity

        inventory.save(
            update_fields=[
                "quantity",
                "reserved_quantity",
                "updated_at",
            ]
        )

    now = timezone.now()

    delivery.status = Delivery.Status.DELIVERED
    delivery.delivered_at = now

    delivery.save(
        update_fields=[
            "status",
            "delivered_at",
            "updated_at",
        ]
    )

    route_stop.status = RouteStop.Status.DELIVERED
    route_stop.completed_at = now

    route_stop.save(
        update_fields=[
            "status",
            "completed_at",
            "updated_at",
        ]
    )

    order.status = order.Status.DELIVERED

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    # If every route stop is now terminal, complete the route.
    remaining_stops = route.stops.exclude(
        status__in=[
            RouteStop.Status.DELIVERED,
            RouteStop.Status.FAILED,
        ]
    ).exists()

    if not remaining_stops:
        if route.vehicle_id is not None:
            vehicle = (
                Vehicle.objects
                .select_for_update()
                .get(pk=route.vehicle_id)
            )

            vehicle.status = Vehicle.Status.AVAILABLE

            vehicle.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        route.status = Route.Status.COMPLETED
        route.completed_at = now

        route.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

    return delivery


@transaction.atomic
def fail_delivery(
    delivery_id,
    failure_reason,
    notes="",
):
    delivery = (
        Delivery.objects
        .select_for_update()
        .get(pk=delivery_id)
    )

    route_stop = (
        RouteStop.objects
        .select_for_update()
        .get(pk=delivery.route_stop_id)
    )

    route = (
        Route.objects
        .select_for_update()
        .get(pk=route_stop.route_id)
    )

    if route.status != Route.Status.IN_PROGRESS:
        raise ValidationError(
            f"Only in-progress routes can fail deliveries. "
            f"Current status: {route.status}."
        )

    if delivery.status != Delivery.Status.IN_PROGRESS:
        raise ValidationError(
            f"Only in-progress deliveries can be failed. "
            f"Current status: {delivery.status}."
        )

    valid_reasons = {
        choice[0]
        for choice in Delivery.FailureReason.choices
    }

    if failure_reason not in valid_reasons:
        raise ValidationError(
            {
                "failure_reason": (
                    "Invalid delivery failure reason."
                )
            }
        )

    now = timezone.now()

    delivery.status = Delivery.Status.FAILED
    delivery.failure_reason = failure_reason
    delivery.failed_at = now
    delivery.notes = notes

    delivery.save(
        update_fields=[
            "status",
            "failure_reason",
            "failed_at",
            "notes",
            "updated_at",
        ]
    )

    route_stop.status = RouteStop.Status.FAILED
    route_stop.failure_reason = failure_reason
    route_stop.notes = notes
    route_stop.completed_at = now

    route_stop.save(
        update_fields=[
            "status",
            "failure_reason",
            "notes",
            "completed_at",
            "updated_at",
        ]
    )

    # A failed delivery does not consume stock.
    # The reservation remains available for a retry/reallocation workflow.

    remaining_stops = route.stops.exclude(
        status__in=[
            RouteStop.Status.DELIVERED,
            RouteStop.Status.FAILED,
        ]
    ).exists()

    if not remaining_stops:
        if route.vehicle_id is not None:
            vehicle = (
                Vehicle.objects
                .select_for_update()
                .get(pk=route.vehicle_id)
            )

            vehicle.status = Vehicle.Status.AVAILABLE

            vehicle.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        route.status = Route.Status.COMPLETED
        route.completed_at = now

        route.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

    return delivery
