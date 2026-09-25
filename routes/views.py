from django.shortcuts import render
from .services import optimize_route, start_route
# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Route, RouteStop
from .serializers import RouteSerializer, RouteStopSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import optimize_route

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
    
    
    @action(
        detail=True,
        methods=["post"],
        url_path="optimize",
    )
    
    def optimize(self, request, pk=None):
        try:
            route = optimize_route(pk)
        except Route.DoesNotExist:
            return Response(
                {"detail": "Route not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(route)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
        
        
    @action(
    detail=True,
    methods=["post"],
    url_path="start",
    )
    def start(self, request, pk=None):
        try:
            route = start_route(pk)
        except Route.DoesNotExist:
            return Response(
                {"detail": "Route not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(route)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


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