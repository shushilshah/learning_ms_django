from rest_framework import status, views
from rest_framework.response import Response
from .serializers import SignupSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken



class SignupAPIView(views.APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Signup successfull",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.userprofile.role
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LoginAPIView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username= request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login Successful",
                "user": {
                    "username": user.username,
                    "role": getattr(user.userprofile, "role", None)                
                    },
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)