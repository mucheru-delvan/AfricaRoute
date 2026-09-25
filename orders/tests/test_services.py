import pytest
from rest_framework.exceptions import ValidationError

from customers.models import Customer
from inventory.models import Inventory
from orders.models import Order
from orders.services import allocate_order, confirm_order
from products.models import Product
from warehouses.models import Warehouse


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="Test Customer",
        customer_type="SUPERMARKET",
        phone_number="0700000000",
        address="Westlands, Nairobi",
        latitude="-1.267600",
        longitude="36.810800",
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Test Coca-Cola",
        sku="TEST-COKE-500",
        unit_price="80.00",
    )


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        name="Test Warehouse",
        code="TEST-DC",
        location="Nairobi",
        address="Nairobi",
        latitude="-1.286389",
        longitude="36.817223",
    )


@pytest.fixture
def inventory(warehouse, product):
    return Inventory.objects.create(
        warehouse=warehouse,
        product=product,
        quantity=1000,
        reserved_quantity=0,
        reorder_level=100,
    )


@pytest.fixture
def order(customer, product):
    order = Order.objects.create(
        customer=customer,
    )

    order.items.create(
        product=product,
        quantity=100,
        unit_price=product.unit_price,
    )

    return order


def test_pending_order_can_be_confirmed(order):
    confirm_order(order.id)

    order.refresh_from_db()

    assert order.status == Order.Status.CONFIRMED


def test_confirming_confirmed_order_fails(order):
    order.status = Order.Status.CONFIRMED
    order.save()

    with pytest.raises(ValidationError):
        confirm_order(order.id)


def test_confirmed_order_can_be_allocated(
    order,
    warehouse,
    inventory,
):
    order.status = Order.Status.CONFIRMED
    order.save()

    allocate_order(order.id)

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == Order.Status.ALLOCATED
    assert order.warehouse_id == warehouse.id
    assert inventory.reserved_quantity == 100


def test_insufficient_inventory_does_not_allocate(
    order,
    inventory,
):
    inventory.quantity = 50
    inventory.save()

    order.status = Order.Status.CONFIRMED
    order.save()

    with pytest.raises(ValidationError):
        allocate_order(order.id)

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == Order.Status.CONFIRMED
    assert inventory.reserved_quantity == 0
