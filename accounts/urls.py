from django.urls import path 
from .views import *







urlpatterns = [
    path('users/', UserGenericView.as_view()),
    path('users/<int:pk>/', UserGenericByOne.as_view()),
    path('otp/verify', OtpVerifyView.as_view()),
    path('login/', LoginView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('change-password/', ResetPasswordView.as_view()),
    path('logout/', LogoutView.as_view()),
    # path('delete-user/', DeleteAccountView.as_view()),

]