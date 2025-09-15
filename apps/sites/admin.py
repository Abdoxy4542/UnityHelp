from django.contrib import admin
from .models import State, Locality, Site


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'name_ar')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_ar')
        }),
        ('Geographic Data', {
            'fields': ('boundary', 'center_point'),
            'description': 'Geographic boundaries and center point stored as GeoJSON'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'state', 'created_at', 'updated_at')
    list_filter = ('state', 'created_at', 'updated_at')
    search_fields = ('name', 'name_ar', 'state__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_ar', 'state')
        }),
        ('Geographic Data', {
            'fields': ('boundary', 'center_point'),
            'description': 'Geographic boundaries and center point stored as GeoJSON'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'site_type', 'operational_status', 'state', 'locality',
                   'total_population', 'total_households', 'report_date')
    list_filter = ('site_type', 'operational_status', 'state', 'locality',
                  'report_date', 'created_at')
    search_fields = ('name', 'name_ar', 'description', 'contact_person',
                    'reported_by', 'locality__name', 'state__name')
    readonly_fields = ('created_at', 'updated_at', 'coordinates', 'longitude',
                      'latitude', 'population_by_age_verified',
                      'population_by_gender_verified', 'average_household_size',
                      'vulnerability_rate', 'child_dependency_ratio')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_ar', 'description', 'site_type', 'operational_status')
        }),
        ('Location', {
            'fields': ('state', 'locality', 'location', 'size_of_location'),
            'description': 'Geographic location and administrative hierarchy'
        }),
        ('Map Coordinates (Read-only)', {
            'fields': ('coordinates', 'longitude', 'latitude'),
            'classes': ('collapse',),
            'description': 'Calculated coordinates from location GeoJSON data'
        }),
        ('Population Demographics', {
            'fields': ('total_population', 'total_households',
                      'children_under_18', 'adults_18_59', 'elderly_60_plus',
                      'male_count', 'female_count'),
            'description': 'Population breakdown by age and gender'
        }),
        ('Vulnerability Data', {
            'fields': ('disabled_count', 'pregnant_women', 'chronically_ill'),
            'description': 'Vulnerable population statistics'
        }),
        ('Contact & Reporting', {
            'fields': ('contact_person', 'contact_phone', 'contact_email',
                      'reported_by', 'report_date'),
        }),
        ('Calculated Statistics (Read-only)', {
            'fields': ('population_by_age_verified', 'population_by_gender_verified',
                      'average_household_size', 'vulnerability_rate',
                      'child_dependency_ratio'),
            'classes': ('collapse',),
            'description': 'Auto-calculated demographic statistics and data validation'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('state', 'locality')
