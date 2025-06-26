from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from .models import OTP
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests
import random
from django.utils import timezone
from datetime import timedelta
# Create your views here.

User = get_user_model()


def generate_otp():

    otp =   random.randint(100000, 999999)
    return otp

class LoginView(APIView):
    @swagger_auto_schema(methods = ['POST'], request_body=LoginSerializer())
    @action(detail=True, methods=['POST'])

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email = serializer.validated_data.get('email'),                                                                                                                                             #type: ignore
            password = serializer.validated_data.get('password')                                                                                                                                             #type: ignore       
        )

        if user:

            token_data = RefreshToken.for_user(user)

            data = {
                "name": user.full_name,                                                                                                                         #type: ignore                                                   
                "refresh": str(token_data),
                "access": str(token_data.access_token)
            }

            return Response(data, status=200)
        
        return Response({"error": "Invalid password or credentials"}, status=400)




class UserGenericView(generics.ListCreateAPIView):

    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]



    def create(self, request, *args, **kwargs):

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        User.objects.create_user(                                                                                                   #type: ignore
            **serializer._validated_data                                                                                            #type: ignore
        )


        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return Response({'error': 'Authentication credentials is not valid'}, status=403)

        users = User.objects.all()

        return Response(UserSerializer(users, many=True).data, status=200)
    

class UserGenericByOne(generics.RetrieveAPIView):

    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'pk'


class OtpVerifyView(APIView):
    @swagger_auto_schema(methods = ['POST'], request_body=OtpSerializer())
    @action(detail=True, methods = ['POST']) 

    def post(self, request):

        serializer = OtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data['otp']                                                                                                                                                  #type: ignore

        if not OTP.objects.filter(otp=otp).exists():
            return Response({'error': 'Invalid OTP'}, status=404)
        
        otp = OTP.objects.get(otp=otp)

        if otp.is_otp_valid():
            
            otp.user.is_active = True
            otp.user.save()

            otp.delete()

            return Response({'message': 'OTP verified successfully'}, status=200)
        
        else:

            otp.delete()

            return Response({'error': 'OTP expired'}, status=400)



class ForgotPasswordView(APIView):
    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']                                                                                                                                                              #type: ignore
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=404)
        
        
        otp_code = generate_otp()
        expiry = timezone.now() + timedelta(minutes=10)
        
       
        OTP.objects.create(
            otp=str(otp_code),
            user=user,
            expiry_date=expiry
        )
        
        url = "https://api.useplunk.com/v1/track"
        headers = {
            "Authorization": "Bearer sk_10c4a02e1119df59dedfc538c730b4e437b997aa7ff781f0",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "event": "password_reset",
            "data": {
                "full_name": user.full_name,                                                                                                                                            #type: ignore
                "otp": str(otp_code)
            }
        }
        response = requests.post(url, headers=headers, json=data)
        print(response.json())
        
        return Response({"message": "OTP sent to your email."})

class ResetPasswordView(APIView):
    @swagger_auto_schema(request_body=ResetPasswordSerializer)
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_code = serializer.validated_data['otp']                                                                                                                                     #type: ignore
        new_password = serializer.validated_data['new_password']                                                                                                                                                            #type: ignore
        
        try:
            otp_obj = OTP.objects.get(otp=otp_code)
        except OTP.DoesNotExist:
            return Response({"error": "Invalid OTP."}, status=404)
        
       
        if not otp_obj.is_otp_valid():
            otp_obj.delete()
            return Response({"error": "OTP has expired."}, status=400)
        
        user = otp_obj.user
        user.set_password(new_password)
        user.save()
        
        
        otp_obj.delete()
        
        return Response({"message": "Password reset successfully."})



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_description="Log out user by blacklisting refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Your refresh token')
            },
            required=['refresh']
        ),
        responses={200: 'Logged out successfully', 400: 'Bad request'}
    )
    def post(self, request):
        user = request.user  
        refresh_token = request.data.get("refresh")
        
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({"message": f"Successfully logged out {user.email}."}, status=200)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=400)