# ===== apps/accounts/models.py =====
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model for UnityAid platform"""
    
    ROLE_CHOICES = [
        ('gso', _('Gathering Site Official')),
        ('ngo_user', _('NGO User')),
        ('un_user', _('UN User')),
        ('cluster_lead', _('Cluster Lead')),
        ('admin', _('Admin')),
        ('public', _('Public User')),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='gso')
    organization = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    # Store location as GeoJSON-like dict in development to avoid GIS dependency
    location = models.JSONField(null=True, blank=True, help_text="User's current location {type: 'Point', coordinates: [lon, lat]}")
    preferred_language = models.CharField(max_length=5, default='en', choices=[('en', 'English'), ('ar', 'Arabic')])
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # GSO specific fields
    assigned_sites = models.ManyToManyField('sites.Site', blank=True, related_name='assigned_gsos')
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    bio = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"

# Create your models here.
