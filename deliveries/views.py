from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Delivery
from .serializers import DeliverySerializer


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = (
        Delivery.objects
        .select_related(
            "route_stop",
            "route_stop__route",
            "route_stop__order",
            "route_stop__order__customer",
        )
    )

    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]