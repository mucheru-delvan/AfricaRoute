from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsDispatcher
from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    #Create a new user
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    #Retrieve the authenticated user's information
    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "role": request.user.role,
            "phone_number": request.user.phone_number,
        })
        
        
class DispatchView(APIView):
    permission_classes = [IsDispatcher]
    #Tests if the authenticated user has the dispatcher role
    def get(self, request):
        return Response({
            "message": "You are a dispatcher."
        })