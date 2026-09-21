

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "items__product",
    ).select_related(
        "customer",
    )

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]