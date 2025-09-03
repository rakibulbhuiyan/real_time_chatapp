from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError
from celery import shared_task
from .tasks import send_otp_email
User = get_user_model()

from django.db import transaction
# ===== Signup Serializer=====
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'confirm_password']

    def validate(self, data):

        if data['password'] != data['confirm_password']:
            raise ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    email=validated_data['email'],
                    password=validated_data['password'],
                    name=validated_data.get('name', ""),
                    is_active=False
                )
                
                # Generate OTP
                user.generate_otp()
                user.save()  # Ensure OTP is saved

                # Send OTP email asynchronously
                send_otp_email.delay(user.email, user.otp)

                return user
        except Exception as e:
            raise ValidationError({"detail": f"Signup failed: {str(e)}"})
    

# ===== Login Serializer=====
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# ===== Profile Serializer=====
# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ['email', 'name', 'profile_pic', 'grade', 'star', 'level', 'is_premium']
    
#     def get_email(self, instance):
#         return instance.user.email
    
#     def update(self, instance, validated_data):
        
#         instance.name = validated_data.get('name', instance.name)
#         instance.profile_pic = validated_data.get('profile_pic', instance.profile_pic)
#         instance.grade = validated_data.get('grade', instance.grade)
#         instance.save()
#         return instance

# ===== Password Reset =====
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        user.generate_otp()
        send_mail(
            "Password Reset OTP",
            f"Your OTP for password reset is {user.otp}",
            "support@softvencefsd.xyz",
            [user.email],
            fail_silently=False,
        )
        return value

class PasswordResetChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data