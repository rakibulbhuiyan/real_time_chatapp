from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import random

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates a regular user after validating email and normalizing it.
        """
        if not email:
            raise ValueError("email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_staffuser(self, email, password=None):
        user = self.create_user(email,
                password=password
        )
        user.is_staff = True
        user.save(using=self._db)
        
        return user
    def create_superuser(self, email, password=None):
        user = self.create_user(email,
                password=password
        )
        user.is_staff = True
        user.is_admin = True
        user.save(using=self._db)
        
        return user



class User(AbstractBaseUser, PermissionsMixin):
    CHOICE_MEDAL = (
    ("bronze", "Bronze"),
    ("silver", "Silver"),
    ("gold", "Gold")
)
    
    email = models.EmailField(unique=True)  # Replaces username
    name = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    grade = models.CharField(max_length=10, blank=True, null=True)

    stars = models.PositiveIntegerField(default=0)
    medal = models.CharField(max_length=10, choices=CHOICE_MEDAL, default="bronze")

    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Admin site access
    is_admin = models.BooleanField(default=False)  # Custom admin flag

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_exp = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)

    reset_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token_exp = models.DateTimeField(null=True, blank=True)

    objects = UserManager()  # Uses the custom manager
    USERNAME_FIELD = 'email'  # Login identifier
    def __str__(self):
        return self.email


    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, if admin
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, if admin
        return self.is_admin 
    

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))  # Generate 6-digit OTP
        self.otp_exp = timezone.now() + timedelta(minutes=10)
        self.otp_verified = False
        self.save()

    def __str__(self):
        return self.email




