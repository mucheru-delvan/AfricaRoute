from django.db import transaction
from rest_framework.exceptions import ValidationError

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
