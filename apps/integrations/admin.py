from django.contrib import admin
from .models import (
    ExternalDataSource, SudanCrisisData, DisplacementData,
    RefugeeData, FundingData, HealthData, DataSyncLog
)


@admin.register(ExternalDataSource)
class ExternalDataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'is_active', 'last_sync', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['name', 'api_endpoint']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SudanCrisisData)
class SudanCrisisDataAdmin(admin.ModelAdmin):
    list_display = ['title', 'data_type', 'source', 'crisis_date', 'location_name', 'created_at']
    list_filter = ['data_type', 'source__platform', 'crisis_date', 'created_at']
    search_fields = ['title', 'description', 'location_name', 'external_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'crisis_date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('source', 'external_id', 'title', 'description', 'data_type')
        }),
        ('Crisis Context', {
            'fields': ('crisis_date', 'report_date', 'url')
        }),
        ('Geographic Data', {
            'fields': ('location_name', 'location_code', 'admin_level')
        }),
        ('Data Content', {
            'fields': ('raw_data', 'processed_data', 'tags'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DisplacementData)
class DisplacementDataAdmin(admin.ModelAdmin):
    list_display = ['crisis_data', 'idp_individuals', 'idp_families', 'departure_location', 'arrival_location']
    list_filter = ['site_type', 'crisis_data__crisis_date']
    search_fields = ['departure_location', 'arrival_location', 'site_name']


@admin.register(RefugeeData)
class RefugeeDataAdmin(admin.ModelAdmin):
    list_display = ['crisis_data', 'refugees', 'asylum_seekers', 'country_of_origin', 'country_of_asylum']
    list_filter = ['country_of_origin', 'country_of_asylum', 'crisis_data__crisis_date']
    search_fields = ['country_of_origin', 'country_of_asylum']


@admin.register(FundingData)
class FundingDataAdmin(admin.ModelAdmin):
    list_display = ['crisis_data', 'requirements', 'funding_received', 'funding_gap', 'donor_country', 'sector']
    list_filter = ['sector', 'donor_country', 'crisis_data__crisis_date']
    search_fields = ['donor_country', 'recipient_organization', 'appeal_name', 'sector']


@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ['crisis_data', 'disease_name', 'cases_reported', 'deaths_reported', 'people_in_need_health']
    list_filter = ['disease_name', 'crisis_data__crisis_date']
    search_fields = ['disease_name']


@admin.register(DataSyncLog)
class DataSyncLogAdmin(admin.ModelAdmin):
    list_display = ['source', 'status', 'sync_start', 'sync_end', 'records_processed', 'records_created']
    list_filter = ['status', 'source__platform', 'sync_start']
    search_fields = ['source__name', 'error_message']
    readonly_fields = ['sync_start', 'sync_end']
    date_hierarchy = 'sync_start'

    fieldsets = (
        ('Sync Information', {
            'fields': ('source', 'status', 'sync_start', 'sync_end')
        }),
        ('Results', {
            'fields': ('records_processed', 'records_created', 'records_updated')
        }),
        ('Date Range', {
            'fields': ('date_from', 'date_to')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )
