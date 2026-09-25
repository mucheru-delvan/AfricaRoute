import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from customers.models import Customer
from deliveries.models import Delivery
from fleet.models import Vehicle
from inventory.models import Inventory
from orders.models import Order
from products.models import Product
from routes.models import Route, RouteStop
from users.models import User
from warehouses.models import Warehouse


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="route_api_user",
        password="TestPassword123!",
        role=User.Role.STAFF,
    )


@pytest.fixture
def authenticated_client(api_client, user):
    refresh = RefreshToken.for_user(user)

    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )

    return api_client


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        name="API Route Warehouse",
        code="API-ROUTE-DC",
        location="Nairobi",
        address="Nairobi",
        latitude="-1.286389",
        longitude="36.817223",
    )


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.create(
        registration_number="API-ROUTE-123",
        vehicle_type=Vehicle.VehicleType.TRUCK,
        capacity=800,
        status=Vehicle.Status.AVAILABLE,
        is_active=True,
    )


@pytest.fixture
def driver(db):
    return User.objects.create_user(
        username="api_route_driver",
        password="TestPassword123!",
        role=User.Role.DRIVER,
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="API Route Product",
        sku="API-ROUTE-001",
        unit_price="80.00",
        is_active=True,
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="API Route Customer",
        customer_type=Customer.CustomerType.SUPERMARKET,
        phone_number="0710000000",
        address="Westlands, Nairobi",
        latitude="-1.267600",
        longitude="36.810800",
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
        status=Route.Status.DRAFT,
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
        recipient_name="API Test Receiver",
        notes="",
    )


def test_unauthenticated_user_cannot_optimize_route(api_client, route):
    response = api_client.post(
        f"/api/routes/{route.id}/optimize/"
    )

    assert response.status_code == 401


def test_authenticated_user_can_optimize_route(
    authenticated_client,
    route,
):
    response = authenticated_client.post(
        f"/api/routes/{route.id}/optimize/"
    )

    assert response.status_code == 200
    assert response.data["status"] == Route.Status.OPTIMIZED
    assert response.data["total_distance_km"] is not None
    assert response.data["estimated_duration_minutes"] is not None


def test_authenticated_user_can_start_route(
    authenticated_client,
    route,
):
    authenticated_client.post(
        f"/api/routes/{route.id}/optimize/"
    )

    response = authenticated_client.post(
        f"/api/routes/{route.id}/start/"
    )

    assert response.status_code == 200
    assert response.data["status"] == Route.Status.IN_PROGRESS

    route.refresh_from_db()

    assert route.status == Route.Status.IN_PROGRESS
    assert route.started_at is not None

    route.vehicle.refresh_from_db()

    assert route.vehicle.status == Vehicle.Status.IN_TRANSIT


def test_authenticated_user_can_start_delivery(
    authenticated_client,
    route,
    delivery,
):
    route.status = Route.Status.IN_PROGRESS
    route.save()

    route.vehicle.status = Vehicle.Status.IN_TRANSIT
    route.vehicle.save()

    response = authenticated_client.post(
        f"/api/deliveries/{delivery.id}/start/"
    )

    assert response.status_code == 200
    assert response.data["status"] == Delivery.Status.IN_PROGRESS

    delivery.refresh_from_db()
    delivery.route_stop.refresh_from_db()

    assert delivery.status == Delivery.Status.IN_PROGRESS
    assert delivery.route_stop.status == RouteStop.Status.ARRIVED


def test_authenticated_user_can_complete_delivery(
    authenticated_client,
    route,
    delivery,
    inventory,
):
    route.status = Route.Status.IN_PROGRESS
    route.save()

    route.vehicle.status = Vehicle.Status.IN_TRANSIT
    route.vehicle.save()

    authenticated_client.post(
        f"/api/deliveries/{delivery.id}/start/"
    )

    response = authenticated_client.post(
        f"/api/deliveries/{delivery.id}/complete/"
    )

    assert response.status_code == 200
    assert response.data["status"] == Delivery.Status.DELIVERED

    delivery.refresh_from_db()
    inventory.refresh_from_db()

    assert delivery.status == Delivery.Status.DELIVERED
    assert inventory.quantity == 900
    assert inventory.reserved_quantity == 0


def test_delivery_completion_updates_order(
    authenticated_client,
    route,
    delivery,
    inventory,
):
    route.status = Route.Status.IN_PROGRESS
    route.save()

    route.vehicle.status = Vehicle.Status.IN_TRANSIT
    route.vehicle.save()

    authenticated_client.post(
        f"/api/deliveries/{delivery.id}/start/"
    )

    authenticated_client.post(
        f"/api/deliveries/{delivery.id}/complete/"
    )

    order = delivery.route_stop.order
    order.refresh_from_db()

    assert order.status == Order.Status.DELIVERED
