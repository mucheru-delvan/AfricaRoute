from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from inventory.models import Inventory
from warehouses.models import Warehouse

from .models import Order


@transaction.atomic
def confirm_order(order_id):
    order = (
        Order.objects
        .select_for_update()
        .select_related("customer")
        .prefetch_related("items__product")
        .get(pk=order_id)
    )

    if order.status != Order.Status.PENDING:
        raise ValidationError(
            f"Only pending orders can be confirmed. "
            f"Current status: {order.status}."
        )

    if not order.customer.is_active:
        raise ValidationError(
            "The customer is not active."
        )

    items = list(order.items.all())

    if not items:
        raise ValidationError(
            "An order must contain at least one item."
        )

    for item in items:
        if not item.product.is_active:
            raise ValidationError(
                f"{item.product.name} is not active."
            )

        if item.quantity <= 0:
            raise ValidationError(
                f"Quantity for {item.product.name} must be greater than zero."
            )

    order.status = Order.Status.CONFIRMED

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return order


@transaction.atomic
def allocate_order(order_id):
    order = (
        Order.objects
        .select_for_update()
        .select_related("customer")
        .prefetch_related("items__product")
        .get(pk=order_id)
    )

    if order.status != Order.Status.CONFIRMED:
        raise ValidationError(
            f"Only confirmed orders can be allocated. "
            f"Current status: {order.status}."
        )

    items = list(order.items.all())

    if not items:
        raise ValidationError(
            "An order must contain at least one item."
        )

    warehouses = (
        Warehouse.objects
        .filter(is_active=True)
        .order_by("id")
    )

    for warehouse in warehouses:
        product_ids = [item.product_id for item in items]

        inventory_records = (
            Inventory.objects
            .select_for_update()
            .filter(
                warehouse=warehouse,
                product_id__in=product_ids,
            )
        )

        inventory_by_product = {
            inventory.product_id: inventory
            for inventory in inventory_records
        }

        can_fulfill = True

        for item in items:
            inventory = inventory_by_product.get(item.product_id)

            if inventory is None:
                can_fulfill = False
                break

            available_quantity = (
                inventory.quantity
                - inventory.reserved_quantity
            )

            if available_quantity < item.quantity:
                can_fulfill = False
                break

        if not can_fulfill:
            continue

        for item in items:
            inventory = inventory_by_product[item.product_id]

            inventory.reserved_quantity += item.quantity

            inventory.save(
                update_fields=[
                    "reserved_quantity",
                    "updated_at",
                ]
            )

        order.warehouse = warehouse
        order.status = Order.Status.ALLOCATED
        order.allocated_at = timezone.now()

        order.save(
            update_fields=[
                "warehouse",
                "status",
                "allocated_at",
                "updated_at",
            ]
        )

        return order

    raise ValidationError(
        "No active warehouse has sufficient inventory "
        "to fulfill this order."
    )
