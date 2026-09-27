# AfricaRoute

**Intelligent Distribution & Route Management API**

AfricaRoute is a Django REST API for managing warehouse-based distribution operations, from order creation and inventory allocation to fleet assignment, route optimization, and delivery execution.

The project models a simplified distribution network in which warehouses fulfill customer orders using available vehicles and drivers. The backend emphasizes transactional integrity, concurrency safety, role-based access control, and realistic operational workflows.

---

## Features

### Authentication & Authorization

* JWT-based authentication with Django REST Framework SimpleJWT
* Custom user model with operational roles:

  * `ADMIN`
  * `DISPATCHER`
  * `DRIVER`
  * `STAFF`
* Role-based permissions for operational endpoints

### Order Management

* Create customer orders with multiple products
* Server-side price snapshots on order items
* Delivery-date and delivery-window validation
* Order lifecycle:

```text
PENDING
   ↓
CONFIRMED
   ↓
ALLOCATED
   ↓
DISPATCHED
   ↓
DELIVERED
```

### Inventory Management

* Warehouse-specific inventory
* Reserved inventory tracking
* Reorder levels
* Database constraints preventing invalid reservations
* Transactional inventory allocation

### Transaction-Safe Allocation

Order allocation uses PostgreSQL transactions and row-level locking to prevent inventory overselling during concurrent requests.

The allocation workflow uses:

```text
transaction.atomic()
        +
select_for_update()
        +
database constraints
```

A dedicated concurrency test verifies that two simultaneous allocation attempts cannot reserve the same inventory.

### Fleet Management

Vehicles support:

* Trucks
* Vans
* Motorcycles

Vehicle states include:

```text
AVAILABLE
ASSIGNED
IN_TRANSIT
MAINTENANCE
INACTIVE
```

Vehicle capacity is considered during route optimization.

### Route Management

Routes connect:

```text
Warehouse
   ↓
Vehicle
   ↓
Driver
   ↓
Route Stops
   ↓
Customer Orders
```

Routes progress through:

```text
DRAFT
   ↓
OPTIMIZED
   ↓
IN_PROGRESS
   ↓
COMPLETED
```

### Route Optimization V1

AfricaRoute currently implements a lightweight heuristic route optimizer using:

* Haversine distance
* Nearest Neighbor
* 2-opt local improvement
* Vehicle-capacity validation
* Route distance calculation
* Estimated travel duration

The optimizer exposes:

```http
POST /api/routes/{id}/optimize/
```

The current implementation is intentionally designed as a foundation for more advanced vehicle-routing algorithms.

### Delivery Execution

Delivery execution is modeled as an operational workflow:

```text
Route
  ↓
Route Stop
  ↓
Delivery
  ↓
Start
  ↓
Complete / Fail
```

Delivery completion:

* deducts inventory
* releases reserved inventory
* marks the order as delivered
* updates the route stop
* completes the route when all stops reach a terminal state
* returns the vehicle to `AVAILABLE`

Failed deliveries preserve inventory rather than deducting stock.

### API Documentation

OpenAPI documentation is generated with `drf-spectacular`.

Available locally at:

```text
/api/docs/       Swagger UI
/api/redoc/      ReDoc
/api/schema/     OpenAPI schema
```

Swagger supports JWT Bearer authentication for testing protected endpoints.

---

## Architecture

```text
                    Client
                      │
                      ▼
                Django REST API
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ▼             ▼              ▼
 Authentication   Business Logic   API Docs
        │             │
        │       ┌─────┼─────────────┐
        │       │     │             │
        ▼       ▼     ▼             ▼
      Users   Orders Inventory     Fleet
                    │
                    ▼
                  Routes
                    │
                    ▼
                 Deliveries
                    │
                    ▼
                PostgreSQL
```

### Domain Model

```text
User
 │
 ├── Dispatcher
 ├── Driver
 └── Staff

Warehouse
 │
 └── Inventory ─── Product

Customer
 │
 └── Order
       │
       └── OrderItem ─── Product

Warehouse
 │
 └── Route
      │
      ├── Vehicle
      ├── Driver
      └── RouteStop
             │
             ├── Order
             └── Delivery
```

---

## Technology Stack

| Technology            | Purpose                    |
| --------------------- | -------------------------- |
| Python 3.14           | Backend language           |
| Django 6.1            | Web framework              |
| Django REST Framework | REST API                   |
| PostgreSQL            | Relational database        |
| SimpleJWT             | JWT authentication         |
| drf-spectacular       | OpenAPI documentation      |
| WhiteNoise            | Static file serving        |
| python-decouple       | Environment configuration  |
| dj-database-url       | Database URL configuration |
| uv                    | Dependency management      |
| pytest                | Automated testing          |
| pytest-django         | Django test integration    |
| Git / GitHub          | Version control            |

---

## Project Structure

```text
AfricaRoute/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── users/
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── products/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── warehouses/
│
├── inventory/
│
├── customers/
│
├── orders/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   └── tests/
│
├── fleet/
│
├── routes/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   └── tests/
│
├── deliveries/
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   └── tests/
│
├── manage.py
├── pyproject.toml
├── uv.lock
├── pytest.ini
├── schema.yml
├── .env.example
└── README.md
```

---

## Business Workflow

A typical distribution workflow looks like:

```text
1. Customer places order
          ↓
2. Order is confirmed
          ↓
3. Inventory is allocated from a warehouse
          ↓
4. Vehicle + driver are assigned to a route
          ↓
5. Route is optimized
          ↓
6. Route starts
          ↓
7. Driver starts delivery
          ↓
8. Delivery is completed or failed
          ↓
9. Inventory and order state are updated
          ↓
10. Route completes and vehicle becomes available
```

---

## API Endpoints

### Authentication

```http
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/
GET  /api/auth/dispatch/
```

### Products

```http
GET    /api/products/
POST   /api/products/
GET    /api/products/{id}/
PUT    /api/products/{id}/
PATCH  /api/products/{id}/
DELETE /api/products/{id}/
```

### Warehouses

```http
GET    /api/warehouses/
POST   /api/warehouses/
GET    /api/warehouses/{id}/
PUT    /api/warehouses/{id}/
PATCH  /api/warehouses/{id}/
DELETE /api/warehouses/{id}/
```

### Inventory

```http
GET    /api/inventory/
POST   /api/inventory/
GET    /api/inventory/{id}/
PUT    /api/inventory/{id}/
PATCH  /api/inventory/{id}/
DELETE /api/inventory/{id}/
```

### Customers

```http
GET    /api/customers/
POST   /api/customers/
GET    /api/customers/{id}/
PUT    /api/customers/{id}/
PATCH  /api/customers/{id}/
DELETE /api/customers/{id}/
```

### Orders

```http
GET  /api/orders/
POST /api/orders/

POST /api/orders/{id}/confirm/
POST /api/orders/{id}/allocate/
```

### Fleet

```http
GET    /api/fleet/
POST   /api/fleet/
GET    /api/fleet/{id}/
PUT    /api/fleet/{id}/
PATCH  /api/fleet/{id}/
DELETE /api/fleet/{id}/
```

### Routes

```http
GET  /api/routes/
POST /api/routes/

POST /api/routes/{id}/optimize/
POST /api/routes/{id}/start/
```

### Route Stops

```http
GET    /api/route-stops/
POST   /api/route-stops/
GET    /api/route-stops/{id}/
PUT    /api/route-stops/{id}/
PATCH  /api/route-stops/{id}/
DELETE /api/route-stops/{id}/
```

### Deliveries

```http
GET  /api/deliveries/
POST /api/deliveries/

POST /api/deliveries/{id}/start/
POST /api/deliveries/{id}/complete/
POST /api/deliveries/{id}/fail/
```

---

## Getting Started

### Prerequisites

* Python 3.14+
* PostgreSQL
* uv
* Git

### Clone the repository

```bash
git clone https://github.com/mucheru-delvan/AfricaRoute.git
cd AfricaRoute
```

### Install dependencies

```bash
uv sync
```

### Configure environment variables

Create a local `.env` file:

```bash
cp .env.example .env
```

Configure the database and Django secret:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=africaroute
DB_USER=africaroute_user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

For production, the application can use a PostgreSQL `DATABASE_URL`.

### Apply migrations

```bash
uv run python manage.py migrate
```

### Create an admin account

```bash
uv run python manage.py createsuperuser
```

### Run the development server

```bash
uv run python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

Swagger:

```text
http://127.0.0.1:8000/api/docs/
```

ReDoc:

```text
http://127.0.0.1:8000/api/redoc/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

---

## Testing

AfricaRoute uses pytest and pytest-django.

Run the full test suite:

```bash
uv run pytest
```

Current test coverage includes:

* Order confirmation
* Inventory allocation
* Insufficient inventory handling
* Concurrent allocation attempts
* Route optimization
* Vehicle capacity validation
* Route API authentication
* Route execution
* Delivery execution
* Inventory deduction
* Failed deliveries
* Order status transitions

Current suite:

```text
29 passed
```

The concurrency test is particularly important because it verifies that simultaneous inventory allocation attempts cannot oversell stock.

---

## Data Integrity & Concurrency

AfricaRoute intentionally uses PostgreSQL database features to protect critical business operations.

### Transaction boundaries

Critical workflows use:

```python
transaction.atomic()
```

### Row-level locking

Inventory and order allocation use:

```python
select_for_update()
```

This ensures that concurrent transactions cannot modify the same inventory state incorrectly.

### Database constraints

Examples include:

```text
warehouse + product → unique inventory record

order + product → unique order item

route + sequence → unique stop position

route + order → unique order assignment
```

Inventory also enforces:

```text
reserved_quantity <= quantity
```

These mechanisms make data integrity a database responsibility rather than relying only on application-level validation.

---

## Route Optimization

The first optimization version uses a heuristic approach:

```text
Customer coordinates
       ↓
Haversine distance
       ↓
Nearest Neighbor
       ↓
2-opt
       ↓
Optimized stop order
```

The optimizer also validates total route load against vehicle capacity.

### Current limitation

The V1 optimizer uses geographic straight-line distance and a fixed average travel speed. It does not yet account for:

* actual road networks
* live traffic
* multiple vehicles in a single optimization run
* sophisticated time-window optimization
* dynamic rerouting

These are planned areas for future iterations.

---

## Security

Security-related features include:

* JWT authentication
* Role-based permissions
* Protected API endpoints
* Password hashing through Django's authentication system
* Environment-based secret configuration
* PostgreSQL transaction handling
* Database constraints
* CSRF configuration
* Production-aware security settings

Sensitive credentials should never be committed to Git.

Use:

```text
.env
```

for local secrets and:

```text
.env.example
```

for configuration templates.

---

## Development Principles

AfricaRoute is intentionally built around backend engineering concepts that matter in real transactional systems:

```text
Business rules
    +
Transactions
    +
Database integrity
    +
Concurrency control
    +
Authentication
    +
Authorization
    +
Testing
    +
API documentation
```

The goal is not simply to expose CRUD endpoints, but to model the operational state transitions that occur in a distribution system.

---

## Roadmap

### Completed

* [x] Project foundation
* [x] JWT authentication
* [x] Role-based access control
* [x] Product management
* [x] Warehouse management
* [x] Inventory management
* [x] Customer management
* [x] Order management
* [x] Transactional inventory allocation
* [x] Fleet management
* [x] Route management
* [x] Route stops
* [x] Route optimization V1
* [x] Delivery execution
* [x] Automated testing
* [x] Concurrency testing
* [x] OpenAPI documentation
* [x] Swagger JWT authorization
* [x] Environment-based configuration
* [x] Production-oriented Django settings

### Future

* [ ] Multi-vehicle route optimization
* [ ] Real road-network distance matrices
* [ ] Delivery time-window optimization
* [ ] Dynamic route recalculation
* [ ] Route and delivery analytics
* [ ] Idempotency for critical operations
* [ ] Structured application logging
* [ ] CI/CD with GitHub Actions
* [ ] Production deployment hardening

---

## Project Status

AfricaRoute is an actively developed backend engineering project focused on distribution operations, transactional business logic, and route optimization.

The application has a working local development environment, automated test suite, and OpenAPI documentation.

---

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for details.
