from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Delivery
from .serializers import DeliverySerializer
from .services import (
    complete_delivery,
    fail_delivery,
    start_delivery,
)


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

    @action(
        detail=True,
        methods=["post"],
        url_path="start",
    )
    def start(self, request, pk=None):
        try:
            delivery = start_delivery(pk)

        except Delivery.DoesNotExist:
            return Response(
                {"detail": "Delivery not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(delivery)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="complete",
    )
    def complete(self, request, pk=None):
        try:
            delivery = complete_delivery(pk)

        except Delivery.DoesNotExist:
            return Response(
                {"detail": "Delivery not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(delivery)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="fail",
    )
    def fail(self, request, pk=None):
        failure_reason = request.data.get(
            "failure_reason"
        )

        notes = request.data.get(
            "notes",
            "",
        )

        if not failure_reason:
            return Response(
                {
                    "failure_reason": (
                        "This field is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            delivery = fail_delivery(
                pk,
                failure_reason,
                notes,
            )

        except Delivery.DoesNotExist:
            return Response(
                {"detail": "Delivery not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(delivery)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )