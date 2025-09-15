# ===== apps/accounts/utils.py =====
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user, verification_code):
    """Send email verification code to user"""
    try:
        subject = 'UnityAid - Email Verification Code'
        
        # Create HTML email content
        html_message = render_to_string('accounts/emails/verification_email.html', {
            'user': user,
            'code': verification_code.code,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_code):
    """Send password reset code to user"""
    try:
        subject = 'UnityAid - Password Reset Code'
        
        # Create HTML email content
        html_message = render_to_string('accounts/emails/password_reset_email.html', {
            'user': user,
            'code': reset_code.code,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False