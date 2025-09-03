
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
@shared_task
def send_otp_email(email, otp):
    send_mail(
        "Signup OTP",
        f"Your OTP is {otp}",
        "support@softvencefsd.xyz",
        [email],
        fail_silently=False,
    )

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

@shared_task
def send_dynamic_email(email, context, email_type="otp"):
    """
    Send dynamic email based on type with custom context
    
    Parameters:
    - email: Recipient email address
    - context: Dictionary with template variables
    - email_type: Type of email (signup_otp, password_reset, promotional, etc.)
    """
    
    # Define subject based on email type
    subject_map = {
        "signup_otp": "Your Signup Verification Code",
        "password_reset": "Password Reset Request",
        "promotional": "Special Offer Just For You!",
        "welcome": "Welcome to Our Service!",
        "notification": "Important Notification"
    }
    
    subject = subject_map.get(email_type, "Message from Our Service")
    
    # Load HTML template
    html_content = render_to_string(f'emails/{email_type}.html', context)
    
    # Create plain text version (strip HTML tags)
    text_content = strip_tags(html_content)
    
    # Send email
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()