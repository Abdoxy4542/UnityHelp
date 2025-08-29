# ===== apps/accounts/admin.py =====
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'organization', 'is_verified', 'is_active']
    list_filter = ['role', 'organization', 'is_verified', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'organization']
    ordering = ['username']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('UnityAid Info'), {
            'fields': ('role', 'organization', 'phone_number', 'location', 'preferred_language', 'is_verified', 'assigned_sites')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('UnityAid Info'), {
            'fields': ('role', 'organization', 'phone_number', 'preferred_language')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'emergency_contact', 'email_notifications', 'created_at']
    list_filter = ['email_notifications', 'sms_notifications', 'push_notifications']
    search_fields = ['user__username', 'user__email']

# Register your models here.
