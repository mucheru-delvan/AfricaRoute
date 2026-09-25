import pytest
from rest_framework.exceptions import ValidationError

from customers.models import Customer
from fleet.models import Vehicle
from orders.models import Order
from products.models import Product
from routes.models import Route, RouteStop
from routes.services import optimize_route
from users.models import User
from warehouses.models import Warehouse


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        name="Test Warehouse",
        code="ROUTE-TEST-DC",
        location="Nairobi",
        address="Nairobi",
        latitude="-1.286389",
        longitude="36.817223",
    )


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.create(
        registration_number="TEST-123",
        vehicle_type=Vehicle.VehicleType.TRUCK,
        capacity=800,
        status=Vehicle.Status.AVAILABLE,
        is_active=True,
    )


@pytest.fixture
def driver(db):
    return User.objects.create_user(
        username="route_driver",
        password="TestPassword123!",
        role=User.Role.DRIVER,
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Test Coca-Cola",
        sku="ROUTE-TEST-COKE",
        description="Test product",
        unit_price="80.00",
        is_active=True,
    )


@pytest.fixture
def customers(db):
    return [
        Customer.objects.create(
            name="Customer A",
            customer_type=Customer.CustomerType.SUPERMARKET,
            phone_number="0700000001",
            address="Westlands, Nairobi",
            latitude="-1.267600",
            longitude="36.810800",
        ),
        Customer.objects.create(
            name="Customer B",
            customer_type=Customer.CustomerType.KIOSK,
            phone_number="0700000002",
            address="Kilimani, Nairobi",
            latitude="-1.292100",
            longitude="36.783600",
        ),
        Customer.objects.create(
            name="Customer C",
            customer_type=Customer.CustomerType.RESTAURANT,
            phone_number="0700000003",
            address="CBD, Nairobi",
            latitude="-1.283300",
            longitude="36.816700",
        ),
    ]


@pytest.fixture
def orders(customers, product, warehouse):
    orders = []

    for customer, quantity in zip(
        customers,
        [100, 200, 150],
    ):
        order = Order.objects.create(
            customer=customer,
            warehouse=warehouse,
            status=Order.Status.ALLOCATED,
        )

        order.items.create(
            product=product,
            quantity=quantity,
            unit_price=product.unit_price,
        )

        orders.append(order)

    return orders


@pytest.fixture
def route(warehouse, vehicle, driver, orders):
    route = Route.objects.create(
        warehouse=warehouse,
        vehicle=vehicle,
        driver=driver,
        status=Route.Status.DRAFT,
        scheduled_date="2026-09-25",
    )

    for sequence, order in enumerate(orders, start=1):
        RouteStop.objects.create(
            route=route,
            order=order,
            sequence=sequence,
        )

    return route


def test_valid_route_is_optimized(route):
    optimize_route(route.id)

    route.refresh_from_db()

    assert route.status == Route.Status.OPTIMIZED
    assert route.total_distance_km is not None
    assert route.total_distance_km > 0
    assert route.estimated_duration_minutes is not None
    assert route.estimated_duration_minutes > 0
    assert route.optimized_at is not None


def test_optimizer_preserves_all_stops(route):
    original_stop_ids = set(
        route.stops.values_list("id", flat=True)
    )

    optimize_route(route.id)

    optimized_stop_ids = set(
        RouteStop.objects.filter(
            route=route
        ).values_list("id", flat=True)
    )

    assert optimized_stop_ids == original_stop_ids

    sequences = list(
        RouteStop.objects.filter(
            route=route
        ).values_list("sequence", flat=True)
    )

    assert set(sequences) == {1, 2, 3}


def test_overloaded_route_is_rejected(route):
    route.vehicle.capacity = 400
    route.vehicle.save()

    with pytest.raises(ValidationError):
        optimize_route(route.id)

    route.refresh_from_db()

    assert route.status == Route.Status.DRAFT
    assert route.total_distance_km is None
    assert route.optimized_at is None


def test_only_draft_routes_can_be_optimized(route):
    route.status = Route.Status.OPTIMIZED
    route.save()

    with pytest.raises(ValidationError):
        optimize_route(route.id)