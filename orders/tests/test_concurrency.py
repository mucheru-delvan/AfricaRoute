import threading
from queue import Queue

import pytest
from django.db import close_old_connections
from rest_framework.exceptions import ValidationError

from customers.models import Customer
from inventory.models import Inventory
from orders.models import Order
from orders.services import allocate_order
from products.models import Product
from warehouses.models import Warehouse


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        name="Concurrency Test Warehouse",
        code="CONCURRENT-DC",
        location="Nairobi",
        address="Nairobi",
        latitude="-1.286389",
        longitude="36.817223",
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Concurrency Test Product",
        sku="CONCURRENT-COKE",
        unit_price="80.00",
        is_active=True,
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="Concurrency Test Customer",
        customer_type=Customer.CustomerType.SUPERMARKET,
        phone_number="0700000099",
        address="Westlands, Nairobi",
        latitude="-1.267600",
        longitude="36.810800",
        is_active=True,
    )


@pytest.fixture
def inventory(warehouse, product):
    return Inventory.objects.create(
        warehouse=warehouse,
        product=product,
        quantity=100,
        reserved_quantity=0,
        reorder_level=10,
    )


@pytest.fixture
def orders(customer, product):
    order_a = Order.objects.create(
        customer=customer,
        status=Order.Status.CONFIRMED,
    )

    order_a.items.create(
        product=product,
        quantity=100,
        unit_price=product.unit_price,
    )

    order_b = Order.objects.create(
        customer=customer,
        status=Order.Status.CONFIRMED,
    )

    order_b.items.create(
        product=product,
        quantity=100,
        unit_price=product.unit_price,
    )

    return order_a, order_b


@pytest.mark.django_db(transaction=True)
def test_concurrent_allocation_does_not_oversell_inventory(
    warehouse,
    product,
    inventory,
    orders,
):
    order_a, order_b = orders

    barrier = threading.Barrier(2)
    results = Queue()

    def allocate(order_id):
        close_old_connections()

        try:
            barrier.wait(timeout=10)

            allocate_order(order_id)

            results.put(("success", order_id))

        except ValidationError:
            results.put(("rejected", order_id))

        except Exception as exc:
            results.put(("error", repr(exc)))

        finally:
            close_old_connections()

    thread_a = threading.Thread(
        target=allocate,
        args=(order_a.id,),
    )

    thread_b = threading.Thread(
        target=allocate,
        args=(order_b.id,),
    )

    thread_a.start()
    thread_b.start()

    thread_a.join(timeout=30)
    thread_b.join(timeout=30)

    assert not thread_a.is_alive()
    assert not thread_b.is_alive()

    outcomes = [
        results.get(timeout=5),
        results.get(timeout=5),
    ]

    successes = [
        result
        for result in outcomes
        if result[0] == "success"
    ]

    rejected = [
        result
        for result in outcomes
        if result[0] == "rejected"
    ]

    errors = [
        result
        for result in outcomes
        if result[0] == "error"
    ]

    assert not errors
    assert len(successes) == 1
    assert len(rejected) == 1

    inventory.refresh_from_db()

    assert inventory.quantity == 100
    assert inventory.reserved_quantity == 100

    order_a.refresh_from_db()
    order_b.refresh_from_db()

    allocated_orders = [
        order
        for order in (order_a, order_b)
        if order.status == Order.Status.ALLOCATED
    ]

    confirmed_orders = [
        order
        for order in (order_a, order_b)
        if order.status == Order.Status.CONFIRMED
    ]

    assert len(allocated_orders) == 1
    assert len(confirmed_orders) == 1