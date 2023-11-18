from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, LogoutSerializer, ResetPasswordSerializer
from django.core.mail import send_mail
from rest_framework.views import APIView
from authentication.models import CustomUser
from django.contrib.auth.hashers import make_password

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        return Response(user_data, status=status.HTTP_201_CREATED)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def reset_password(request):
    email = request.data.get("email")
    password = request.data.get("new_password")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if not len(password) >= 8:
        return Response({"data":"Password Should be greater or equal to 8 characters"}, status=status.HTTP_400_BAD_REQUEST)
    if not user_obj:
        return Response({"Error":"Email Address could not be found."}, status=status.HTTP_400_BAD_REQUEST)
    user_obj = CustomUser.objects.get(email=email)
    user_obj.password = make_password(password)
    user_obj.save()
    return Response({"data":"Password Reset Successful"}, status=status.HTTP_201_CREATED)
