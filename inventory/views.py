# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Inventory
from .serializers import InventorySerializer


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related(
        "warehouse",
        "product",
    )
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]