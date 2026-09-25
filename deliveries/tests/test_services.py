import pytest
from rest_framework.exceptions import ValidationError

from customers.models import Customer
from deliveries.models import Delivery
from deliveries.services import (
    complete_delivery,
    fail_delivery,
    start_delivery,
)
from fleet.models import Vehicle
from inventory.models import Inventory
from orders.models import Order
from products.models import Product
from routes.models import Route, RouteStop
from users.models import User
from warehouses.models import Warehouse


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        name="Test Warehouse",
        code="DELIVERY-TEST-DC",
        location="Nairobi",
        address="Nairobi",
        latitude="-1.286389",
        longitude="36.817223",
    )


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.create(
        registration_number="DEL-123",
        vehicle_type=Vehicle.VehicleType.TRUCK,
        capacity=800,
        status=Vehicle.Status.IN_TRANSIT,
        is_active=True,
    )


@pytest.fixture
def driver(db):
    return User.objects.create_user(
        username="delivery_driver",
        password="TestPassword123!",
        role=User.Role.DRIVER,
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="Test Customer",
        customer_type=Customer.CustomerType.SUPERMARKET,
        phone_number="0700000000",
        address="Westlands, Nairobi",
        latitude="-1.267600",
        longitude="36.810800",
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Test Coca-Cola",
        sku="DELIVERY-TEST-COKE",
        unit_price="80.00",
        is_active=True,
    )


@pytest.fixture
def order(warehouse, customer, product):
    order = Order.objects.create(
        customer=customer,
        warehouse=warehouse,
        status=Order.Status.ALLOCATED,
    )

    order.items.create(
        product=product,
        quantity=100,
        unit_price=product.unit_price,
    )

    return order


@pytest.fixture
def inventory(warehouse, product):
    return Inventory.objects.create(
        warehouse=warehouse,
        product=product,
        quantity=1000,
        reserved_quantity=100,
        reorder_level=100,
    )


@pytest.fixture
def route(warehouse, vehicle, driver, order):
    route = Route.objects.create(
        warehouse=warehouse,
        vehicle=vehicle,
        driver=driver,
        status=Route.Status.IN_PROGRESS,
        scheduled_date="2026-09-25",
    )

    RouteStop.objects.create(
        route=route,
        order=order,
        sequence=1,
    )

    return route


@pytest.fixture
def delivery(route):
    route_stop = route.stops.get()

    return Delivery.objects.create(
        route_stop=route_stop,
        recipient_name="Test Receiver",
        notes="",
    )


def test_pending_delivery_can_be_started(delivery, route):
    start_delivery(delivery.id)

    delivery.refresh_from_db()
    route_stop = delivery.route_stop
    route_stop.refresh_from_db()

    assert delivery.status == Delivery.Status.IN_PROGRESS
    assert route_stop.status == RouteStop.Status.ARRIVED
    assert route_stop.arrived_at is not None


def test_completed_delivery_deducts_inventory(
    delivery,
    route,
    inventory,
):
    start_delivery(delivery.id)

    complete_delivery(delivery.id)

    delivery.refresh_from_db()
    inventory.refresh_from_db()

    assert delivery.status == Delivery.Status.DELIVERED
    assert delivery.delivered_at is not None

    assert inventory.quantity == 900
    assert inventory.reserved_quantity == 0


def test_completed_delivery_marks_order_delivered(
    delivery,
    inventory,
):
    start_delivery(delivery.id)

    complete_delivery(delivery.id)

    order = delivery.route_stop.order
    order.refresh_from_db()

    route_stop = delivery.route_stop
    route_stop.refresh_from_db()

    assert order.status == Order.Status.DELIVERED
    assert route_stop.status == RouteStop.Status.DELIVERED
    assert route_stop.completed_at is not None


def test_completed_final_stop_completes_route(
    delivery,
    route,
    inventory,
):
    start_delivery(delivery.id)

    complete_delivery(delivery.id)

    route.refresh_from_db()

    route_vehicle = route.vehicle
    route_vehicle.refresh_from_db()

    assert route.status == Route.Status.COMPLETED
    assert route.completed_at is not None
    assert route_vehicle.status == Vehicle.Status.AVAILABLE


def test_failed_delivery_does_not_deduct_inventory(
    delivery,
    route,
    inventory,
):
    start_delivery(delivery.id)

    fail_delivery(
        delivery.id,
        Delivery.FailureReason.CUSTOMER_UNAVAILABLE,
        "Customer was unavailable.",
    )

    delivery.refresh_from_db()
    inventory.refresh_from_db()

    route_stop = delivery.route_stop
    route_stop.refresh_from_db()

    assert delivery.status == Delivery.Status.FAILED
    assert delivery.failure_reason == (
        Delivery.FailureReason.CUSTOMER_UNAVAILABLE
    )

    assert route_stop.status == RouteStop.Status.FAILED

    assert inventory.quantity == 1000
    assert inventory.reserved_quantity == 100


def test_failed_delivery_does_not_mark_order_delivered(
    delivery,
):
    start_delivery(delivery.id)

    fail_delivery(
        delivery.id,
        Delivery.FailureReason.CUSTOMER_UNAVAILABLE,
    )

    order = delivery.route_stop.order
    order.refresh_from_db()

    assert order.status == Order.Status.ALLOCATED


def test_delivery_cannot_be_completed_before_starting(
    delivery,
):
    with pytest.raises(ValidationError):
        complete_delivery(delivery.id)


def test_delivery_cannot_be_completed_twice(
    delivery,
    inventory,
):
    start_delivery(delivery.id)
    complete_delivery(delivery.id)

    with pytest.raises(ValidationError):
        complete_delivery(delivery.id)

    inventory.refresh_from_db()

    assert inventory.quantity == 900
    assert inventory.reserved_quantity == 0
