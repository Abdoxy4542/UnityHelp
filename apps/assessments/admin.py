from django.contrib import admin
from .models import Assessment, AssessmentResponse, KoboIntegrationSettings


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'assessment_type', 'status', 'created_by', 'start_date', 'end_date', 'response_count']
    list_filter = ['assessment_type', 'status', 'start_date', 'end_date']
    search_fields = ['title', 'title_ar', 'description']
    filter_horizontal = ['target_sites', 'assigned_to']
    readonly_fields = ['created_at', 'updated_at', 'response_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'title_ar', 'description', 'assessment_type', 'status')
        }),
        ('Kobo Integration', {
            'fields': ('kobo_form_id', 'kobo_form_url', 'kobo_username'),
            'classes': ('collapse',)
        }),
        ('Assignment', {
            'fields': ('target_sites', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'response_count'),
            'classes': ('collapse',)
        })
    )


@admin.register(AssessmentResponse)
class AssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'site', 'respondent', 'is_submitted', 'submitted_at', 'created_at']
    list_filter = ['is_submitted', 'submitted_at', 'assessment__assessment_type']
    search_fields = ['assessment__title', 'site__name', 'respondent__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('assessment', 'site', 'respondent')
        }),
        ('Kobo Data', {
            'fields': ('kobo_submission_id', 'kobo_data'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_submitted', 'submitted_at', 'gps_location')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(KoboIntegrationSettings)
class KoboIntegrationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'kobo_username', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'kobo_username']
    readonly_fields = ['created_at', 'updated_at']
