from datetime import timedelta
import uuid
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            user = self.user
            print(user)

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                }
            })
        
        except OAuth2Error as e:
            return Response({
                "error": "Access token expired or invalid. Please login again.",
                "detail": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



User = get_user_model()

# ===== Helper Function =====
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class BaseAPIView(APIView):
    def success_response(self, message="Your request Accepted", data=None, status_code=status.HTTP_200_OK):
        return Response(
            {"success": True, "message": message, "status": status_code, "data": data or {}},
            status=status_code
        )

    def error_response(self, message="Your request rejected", data=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response(
            {"success": False, "message": message, "status": status_code, "data": data or {}},
            status=status_code
        )

# ===== Signup =====
class SignupView(BaseAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = User.objects.filter(email=request.data.get("email")).first()
        if user and not user.is_active:
            user.delete()
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return self.success_response(
                "User created successfully. Please verify OTP.",
                data={"email": user.email}
            )
        return self.error_response(serializer.errors)

class SignupOTPVerifyView(BaseAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        otp = request.data.get("otp")
        if not otp:
            return self.error_response("OTP is required.")

        try:
            user = User.objects.get(
                otp=otp,
                otp_exp__gte=timezone.now(),
                otp_verified=False
            )
        except User.DoesNotExist:
            return self.error_response("Invalid or expired OTP.")

        #  Make user active
        user.is_active = True
        user.otp_verified = True
        user.otp = None
        user.otp_exp = None

        user.save()

        tokens = get_tokens_for_user(user)

        return self.success_response(
            "OTP verified successfully.",
            data={"tokens": tokens}
        )


class LoginView(BaseAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                tokens = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }

                return self.success_response(
                    "Login successful",
                    data={
                        "user": {
                            "id": user.id,
                            "email": user.email,
                        },
                        "tokens": tokens
                    },
                    status_code=status.HTTP_200_OK
                )
            return self.error_response("Invalid email or password", status_code=status.HTTP_401_UNAUTHORIZED)
        return self.error_response("Validation error", data=serializer.errors)


# class ProfileView(BaseAPIView):
#     permission_classes = [permissions.AllowAny]

#     def get(self, request):
#         try:
#             user = request.user
#             serializer = ProfileSerializer(user)
#             return self.success_response(data=serializer.data)
#         except Exception as e:
#             return self.error_response(
#                 "Failed to retrieve profile.",
#                 data={"detail": str(e)}
#             )

#     def put(self, request):
#         user = request.user

#         # Only allow updating the 'grade' field
#         grade = request.data.get('grade')
#         if grade is None:
#             return self.error_response("No grade provided.")

#         serializer = ProfileSerializer(user, data={'grade': grade}, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return self.success_response("Grade updated successfully.", data=serializer.data)
#         return self.error_response("Validation error", data=serializer.errors)


# ===== Password Reset =====

class PasswordResetRequestAPIView(BaseAPIView):
    # permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            return self.success_response("OTP sent to email.", data={"email": serializer.validated_data["email"]})
        return self.error_response("Validation error", data=serializer.errors)

class PasswordResetOTPVerifyView(BaseAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        otp = request.data.get("otp")
        email = request.data.get("email")

        if not otp or not email:
            return self.error_response("Email and OTP are required.")

        try:
            user = User.objects.get(
                email=email,
                otp=otp,
                otp_exp__gte=timezone.now(),
                otp_verified=False
            )
        except User.DoesNotExist:
            return self.error_response("Invalid or expired OTP.")

        # Mark OTP as verified
        user.otp_verified = True
        user.save()

        # Generate temporary reset token (UUID)
        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token   # add this field in User model
        user.reset_token_exp = timezone.now() + timezone.timedelta(minutes=15)
        user.save()

        return self.success_response(
            "OTP verified successfully. Use the reset token to change password.",
            data={"reset_token": reset_token, "email": user.email}
        )


class PasswordResetChangeAPIView(BaseAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        reset_token = request.data.get("reset_token")
        email = request.data.get("email")
        serializer = PasswordResetChangeSerializer(data=request.data)

        if not reset_token or not email:
            return self.error_response("Reset token and email are required.")

        try:
            user = User.objects.get(
                email=email,
                reset_token=reset_token,
                reset_token_exp__gte=timezone.now(),
                otp_verified=True
            )
        except User.DoesNotExist:
            return self.error_response("Invalid or expired reset token.")

        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            # Clear OTP + reset token
            user.otp_verified = False
            user.otp = None
            user.otp_exp = None
            user.reset_token = None
            user.reset_token_exp = None
            user.save()
            return self.success_response("Password reset successful.")

        return self.error_response("Validation error", data=serializer.errors)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": f"Logout failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        

        
from rest_framework import generics

class ChangePasswordView(BaseAPIView, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def put(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation error", data=serializer.errors)

        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return self.error_response("Old password does not match")

        user.set_password(new_password)
        user.save()
        return self.success_response("Password changed successfully")


