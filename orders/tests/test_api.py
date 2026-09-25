import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from customers.models import Customer
from inventory.models import Inventory
from orders.models import Order
from products.models import Product
from users.models import User
from warehouses.models import Warehouse


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="api_user",
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
def customer(db):
    return Customer.objects.create(
        name="API Test Customer",
        customer_type=Customer.CustomerType.SUPERMARKET,
        phone_number="0700000010",
        email="api@example.com",
        address="Westlands, Nairobi",
        latitude="-1.267600",
        longitude="36.810800",
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="API Test Coca-Cola",
        sku="API-TEST-COKE",
        description="API test product",
        unit_price="80.00",
        is_active=True,
    )


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        name="API Test Warehouse",
        code="API-TEST-DC",
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
def order(
    customer,
    product,
):
    order = Order.objects.create(
        customer=customer,
    )

    order.items.create(
        product=product,
        quantity=100,
        unit_price=product.unit_price,
    )

    return order


def test_unauthenticated_user_cannot_list_orders(api_client):
    response = api_client.get(
        "/api/orders/"
    )

    assert response.status_code == 401


def test_authenticated_user_can_list_orders(
    authenticated_client,
):
    response = authenticated_client.get(
        "/api/orders/"
    )

    assert response.status_code == 200


def test_authenticated_user_can_create_order(
    authenticated_client,
    customer,
    product,
):
    payload = {
        "customer": customer.id,
        "requested_delivery_date": "2026-09-25",
        "delivery_window_start": "09:00:00",
        "delivery_window_end": "11:00:00",
        "items": [
            {
                "product": product.id,
                "quantity": 100,
            }
        ],
    }

    response = authenticated_client.post(
        "/api/orders/",
        payload,
        format="json",
    )

    assert response.status_code == 201

    assert response.data["customer"] == customer.id
    assert response.data["status"] == Order.Status.PENDING
    assert len(response.data["items"]) == 1

    assert response.data["items"][0]["product"] == product.id
    assert response.data["items"][0]["quantity"] == 100
    assert response.data["items"][0]["unit_price"] == "80.00"


def test_confirm_endpoint_changes_order_status(
    authenticated_client,
    order,
):
    response = authenticated_client.post(
        f"/api/orders/{order.id}/confirm/"
    )

    assert response.status_code == 200
    assert response.data["status"] == Order.Status.CONFIRMED


def test_confirm_endpoint_rejects_already_confirmed_order(
    authenticated_client,
    order,
):
    order.status = Order.Status.CONFIRMED
    order.save()

    response = authenticated_client.post(
        f"/api/orders/{order.id}/confirm/"
    )

    assert response.status_code == 400


def test_allocate_endpoint_reserves_inventory(
    authenticated_client,
    order,
    warehouse,
    inventory,
):
    order.status = Order.Status.CONFIRMED
    order.save()

    response = authenticated_client.post(
        f"/api/orders/{order.id}/allocate/"
    )

    assert response.status_code == 200
    assert response.data["status"] == Order.Status.ALLOCATED
    assert response.data["warehouse"] == warehouse.id

    inventory.refresh_from_db()

    assert inventory.reserved_quantity == 100
