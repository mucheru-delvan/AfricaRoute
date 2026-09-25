import math
from decimal import Decimal
from fleet.models import Vehicle
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from orders.models import Order

from .models import Route, RouteStop


AVERAGE_SPEED_KMPH = 30.0


def customer_location(stop):
    customer = stop.order.customer

    return (
        float(customer.latitude),
        float(customer.longitude),
    )


def haversine_distance(point_a, point_b):
    """
    Calculate straight-line geographic distance
    between two latitude/longitude points in kilometres.
    """

    lat1, lon1 = point_a
    lat2, lon2 = point_b

    earth_radius_km = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius_km * c


def distance_from_depot(depot, stop):
    return haversine_distance(
        depot,
        customer_location(stop),
    )


def distance_between_stops(stop_a, stop_b):
    return haversine_distance(
        customer_location(stop_a),
        customer_location(stop_b),
    )


def route_distance(depot, stops):
    """
    Calculate:

    depot → stop 1 → stop 2 → ... → depot
    """

    if not stops:
        return 0.0

    total_distance = 0.0

    total_distance += distance_from_depot(
        depot,
        stops[0],
    )

    for index in range(len(stops) - 1):
        total_distance += distance_between_stops(
            stops[index],
            stops[index + 1],
        )

    total_distance += distance_from_depot(
        depot,
        stops[-1],
    )

    return total_distance


def nearest_neighbor(depot, stops):
    """
    Construct an initial route by repeatedly selecting
    the nearest unvisited RouteStop.
    """

    remaining = list(stops)
    ordered = []

    current = depot
    current_stop = None

    while remaining:
        if current_stop is None:
            nearest = min(
                remaining,
                key=lambda stop: distance_from_depot(
                    current,
                    stop,
                ),
            )
        else:
            nearest = min(
                remaining,
                key=lambda stop: distance_between_stops(
                    current_stop,
                    stop,
                ),
            )

        ordered.append(nearest)
        remaining.remove(nearest)
        current_stop = nearest

    return ordered


def two_opt(depot, stops):
    """
    Improve the route by reversing route segments
    when doing so reduces total distance.
    """

    if len(stops) < 3:
        return list(stops)

    best_route = list(stops)

    best_distance = route_distance(
        depot,
        best_route,
    )

    improved = True

    while improved:
        improved = False

        for i in range(len(best_route) - 1):
            for j in range(i + 2, len(best_route) + 1):
                new_route = (
                    best_route[:i]
                    + best_route[i:j][::-1]
                    + best_route[j:]
                )

                new_distance = route_distance(
                    depot,
                    new_route,
                )

                if new_distance < best_distance:
                    best_route = new_route
                    best_distance = new_distance
                    improved = True

    return best_route


@transaction.atomic
def optimize_route(route_id):
    route = (
        Route.objects
        .select_for_update()
        .select_related("warehouse")
        .get(pk=route_id)
    )

    if route.status != Route.Status.DRAFT:
        raise ValidationError(
            f"Only draft routes can be optimized. "
            f"Current status: {route.status}."
        )

    if not route.warehouse.is_active:
        raise ValidationError(
            "The route warehouse is not active."
        )

    if route.vehicle_id is None:
        raise ValidationError(
            "A vehicle must be assigned before optimization."
        )

    vehicle = route.vehicle

    if not vehicle.is_active:
        raise ValidationError(
            "The assigned vehicle is not active."
        )

    stops = list(
        route.stops
        .select_related(
            "order",
            "order__customer",
        )
        .prefetch_related(
            "order__items",
        )
    )

    if not stops:
        raise ValidationError(
            "A route must contain at least one stop."
        )

    # Make sure every stop is unique.
    stop_ids = [stop.id for stop in stops]

    if len(stop_ids) != len(set(stop_ids)):
        raise ValidationError(
            "The route contains duplicate stops."
        )

    total_load = 0

    for stop in stops:
        order = stop.order

        if order.status != Order.Status.ALLOCATED:
            raise ValidationError(
                f"Order {order.id} is not allocated."
            )

        if order.warehouse_id != route.warehouse_id:
            raise ValidationError(
                f"Order {order.id} belongs to a different warehouse."
            )

        total_load += sum(
            item.quantity
            for item in order.items.all()
        )

    if total_load > vehicle.capacity:
        raise ValidationError(
            f"Route load is {total_load}, but vehicle "
            f"capacity is only {vehicle.capacity}."
        )

    depot = (
        float(route.warehouse.latitude),
        float(route.warehouse.longitude),
    )

    # Build initial route.
    initial_route = nearest_neighbor(
        depot,
        stops,
    )

    # Improve initial route.
    optimized_stops = two_opt(
        depot,
        initial_route,
    )

    # Verify that optimization did not lose or duplicate stops.
    optimized_ids = [stop.id for stop in optimized_stops]

    if set(optimized_ids) != set(stop_ids):
        raise ValidationError(
            "Route optimization produced an invalid set of stops."
        )

    if len(optimized_ids) != len(set(optimized_ids)):
        raise ValidationError(
            "Route optimization produced duplicate stops."
        )

    final_distance = route_distance(
        depot,
        optimized_stops,
    )

    estimated_duration = math.ceil(
        (final_distance / AVERAGE_SPEED_KMPH) * 60
    )

    # ---------------------------------------------------------
    # Safely replace existing sequence values.
    # ---------------------------------------------------------

    highest_sequence = max(
        stop.sequence
        for stop in stops
    )

    temporary_base = (
        highest_sequence
        + len(stops)
        + 1000
    )

    # First move every stop away from the real sequence range.
    for index, stop in enumerate(
        stops,
        start=1,
    ):
        stop.sequence = temporary_base + index

        stop.save(
            update_fields=["sequence"]
        )

    # Now assign the optimized sequence.
    for index, stop in enumerate(
        optimized_stops,
        start=1,
    ):
        stop.sequence = index

        stop.save(
            update_fields=["sequence"]
        )

    route.total_distance_km = Decimal(
        str(round(final_distance, 2))
    )

    route.estimated_duration_minutes = (
        estimated_duration
    )

    route.optimized_at = timezone.now()

    route.status = Route.Status.OPTIMIZED

    route.save(
        update_fields=[
            "total_distance_km",
            "estimated_duration_minutes",
            "optimized_at",
            "status",
            "updated_at",
        ]
    )

    return route

@transaction.atomic
def start_route(route_id):
    route = (
        Route.objects
        .select_for_update()
        .get(pk=route_id)
    )

    if route.status != Route.Status.OPTIMIZED:
        raise ValidationError(
            f"Only optimized routes can be started. "
            f"Current status: {route.status}."
        )

    if route.vehicle_id is None:
        raise ValidationError(
            "A vehicle must be assigned before starting."
        )

    if route.driver_id is None:
        raise ValidationError(
            "A driver must be assigned before starting."
        )

    if not route.stops.exists():
        raise ValidationError(
            "A route must contain at least one stop."
        )

    vehicle = (
        Vehicle.objects
        .select_for_update()
        .get(pk=route.vehicle_id)
    )

    if not vehicle.is_active:
        raise ValidationError(
            "The assigned vehicle is not active."
        )

    if vehicle.status != Vehicle.Status.AVAILABLE:
        raise ValidationError(
            f"Vehicle is not available. "
            f"Current status: {vehicle.status}."
        )

    route.status = Route.Status.IN_PROGRESS
    route.started_at = timezone.now()

    vehicle.status = Vehicle.Status.IN_TRANSIT

    vehicle.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    route.save(
        update_fields=[
            "status",
            "started_at",
            "updated_at",
        ]
    )

    return route