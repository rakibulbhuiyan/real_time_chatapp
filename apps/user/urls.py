from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Signup
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", SignupOTPVerifyView.as_view(), name="signup-verify-otp"),

    # Login & Profile
    path("login/", LoginView.as_view(), name="login"),
    # path("profile/", ProfileView.as_view(), name="profile"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Password Reset
    path("password-reset/request/", PasswordResetRequestAPIView.as_view(), name="password-reset-request"),
    path("password-reset/verify-otp/", PasswordResetOTPVerifyView.as_view(), name="password-reset-verify-otp"),
    path("password-reset/change-password/", PasswordResetChangeAPIView.as_view(), name="password-reset-change"),

    # Change Password
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),

    # Logout
    path("logout/", LogoutView.as_view(), name="logout"),
]
