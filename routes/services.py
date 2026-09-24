import math
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Route


AVERAGE_SPEED_KMPH = 30.0


def haversine_distance(point_a, point_b):
    """
    Calculate approximate straight-line distance between
    two latitude/longitude points in kilometres.
    """

    lat1, lon1 = point_a
    lat2, lon2 = point_b

    earth_radius_km = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

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


def route_distance(depot, stops):
    """
    Calculate total round-trip distance:

    depot → stop 1 → stop 2 → ... → depot
    """

    if not stops:
        return 0.0

    total_distance = 0.0
    current = depot

    for stop in stops:
        total_distance += haversine_distance(
            current,
            stop,
        )
        current = stop

    total_distance += haversine_distance(
        current,
        depot,
    )

    return total_distance


def nearest_neighbor(depot, stops):
    """
    Build an initial route by repeatedly selecting
    the nearest unvisited stop.
    """

    remaining = list(stops)
    ordered = []

    current = depot

    while remaining:
        nearest = min(
            remaining,
            key=lambda stop: haversine_distance(
                current,
                stop,
            ),
        )

        ordered.append(nearest)
        remaining.remove(nearest)
        current = nearest

    return ordered


def two_opt(depot, stops):
    """
    Improve an existing route by reversing route segments
    whenever the change reduces total distance.
    """

    if len(stops) < 3:
        return stops

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

    if route.vehicle is None:
        raise ValidationError(
            "A vehicle must be assigned before optimization."
        )

    if not route.vehicle.is_active:
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

    total_load = 0

    for stop in stops:
        order = stop.order

        if order.status != "ALLOCATED":
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

    if total_load > route.vehicle.capacity:
        raise ValidationError(
            f"Route load is {total_load}, but vehicle "
            f"capacity is only {route.vehicle.capacity}."
        )

    depot = (
        float(route.warehouse.latitude),
        float(route.warehouse.longitude),
    )

    stop_locations = []

    for stop in stops:
        customer = stop.order.customer

        location = (
            float(customer.latitude),
            float(customer.longitude),
        )

        stop_locations.append(
            (stop, location)
        )

    location_map = {
        stop.id: location
        for stop, location in stop_locations
    }

    initial = nearest_neighbor(
        depot,
        [
            location_map[stop.id]
            for stop, _ in stop_locations
        ],
    )

    stop_by_location = {
        location: stop
        for stop, location in stop_locations
    }

    optimized_locations = two_opt(
        depot,
        initial,
    )

    optimized_stops = [
        stop_by_location[location]
        for location in optimized_locations
    ]

    final_distance = route_distance(
        depot,
        optimized_locations,
    )

    estimated_duration = math.ceil(
        (final_distance / AVERAGE_SPEED_KMPH) * 60
    )

    # Temporarily move sequences away from existing values
    # so the unique(route, sequence) constraint is not violated.
    temporary_base = 1_000_000

    for index, stop in enumerate(optimized_stops, start=1):
        stop.sequence = temporary_base + index

    RouteStop = stops[0].__class__

    RouteStop.objects.bulk_update(
        optimized_stops,
        ["sequence"],
    )

    for index, stop in enumerate(optimized_stops, start=1):
        stop.sequence = index

    RouteStop.objects.bulk_update(
        optimized_stops,
        ["sequence"],
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
