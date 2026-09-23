from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Route, RouteStop
from .serializers import RouteSerializer, RouteStopSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = (
        Route.objects
        .select_related(
            "warehouse",
            "vehicle",
            "driver",
        )
        .prefetch_related(
            "stops__order__customer",
        )
    )

    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]


class RouteStopViewSet(viewsets.ModelViewSet):
    queryset = (
        RouteStop.objects
        .select_related(
            "route",
            "order",
            "order__customer",
        )
        .order_by(
            "route_id",
            "sequence",
        )
    )

    serializer_class = RouteStopSerializer
    permission_classes = [IsAuthenticated]