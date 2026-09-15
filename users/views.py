from rest_framework.views import APIView
from rest_framework.response import Response

from users.permissions import IsDispatcher


class DispatchView(APIView):
    permission_classes = [IsDispatcher]

    def get(self, request):
        return Response({
            "message": "You are a dispatcher."
        })