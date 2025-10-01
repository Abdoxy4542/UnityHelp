from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class MobileDevice(models.Model):
    """Model to track mobile devices for push notifications and security"""
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_devices')
    device_id = models.CharField(max_length=255, unique=True, help_text="Unique device identifier")
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    fcm_token = models.TextField(blank=True, help_text="Firebase Cloud Messaging token")
    app_version = models.CharField(max_length=20, blank=True)
    os_version = models.CharField(max_length=20, blank=True)
    device_model = models.CharField(max_length=100, blank=True)

    # Security and tracking
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mobile Device'
        verbose_name_plural = 'Mobile Devices'
        unique_together = ['user', 'device_id']

    def __str__(self):
        return f"{self.user.username} - {self.platform} ({self.device_model})"


class RefreshToken(models.Model):
    """Refresh token for mobile authentication"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='refresh_tokens')
    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_revoked and not self.is_expired()

    def __str__(self):
        return f"Refresh token for {self.user.username}"


class SyncLog(models.Model):
    """Track synchronization activities for offline support"""
    SYNC_TYPES = [
        ('initial', 'Initial Sync'),
        ('incremental', 'Incremental Sync'),
        ('upload', 'Data Upload'),
        ('download', 'Data Download'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sync_logs')
    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Sync details
    total_items = models.PositiveIntegerField(default=0)
    processed_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)

    # Metadata
    error_message = models.TextField(blank=True)
    sync_data = models.JSONField(null=True, blank=True, help_text="Additional sync metadata")

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-started_at']

    @property
    def progress_percentage(self):
        if self.total_items == 0:
            return 0
        return round((self.processed_items / self.total_items) * 100, 2)

    def __str__(self):
        return f"{self.sync_type} sync for {self.user.username} - {self.status}"