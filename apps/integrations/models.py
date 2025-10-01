from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date

User = get_user_model()


def get_crisis_start_date():
    """Return Sudan crisis start date"""
    return date(2023, 4, 15)


def get_current_date():
    """Return current date"""
    return date.today()


class ExternalDataSource(models.Model):
    """Base model for external humanitarian data sources"""
    PLATFORM_CHOICES = [
        ('hdx', 'Humanitarian Data Exchange'),
        ('iom_dtm', 'IOM Displacement Tracking Matrix'),
        ('unhcr', 'UNHCR Refugee Data'),
        ('fts', 'OCHA Financial Tracking Service'),
        ('who', 'WHO Health Data'),
        ('acaps', 'ACAPS Analysis'),
        ('wfp', 'World Food Programme'),
        ('fews_net', 'FEWS NET'),
        ('humanitarian_action', 'Humanitarian Action Info'),
    ]

    name = models.CharField(max_length=200)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    api_endpoint = models.URLField()
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_frequency_hours = models.PositiveIntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_external_data_source'

    def __str__(self):
        return f"{self.get_platform_display()} - {self.name}"


class SudanCrisisData(models.Model):
    """Model for storing Sudan crisis data from external sources"""
    DATA_TYPE_CHOICES = [
        ('displacement', 'Displacement & Population'),
        ('food_security', 'Food Security'),
        ('health', 'Health & Disease'),
        ('funding', 'Humanitarian Funding'),
        ('conflict', 'Conflict & Security'),
        ('access', 'Humanitarian Access'),
        ('needs', 'Humanitarian Needs Assessment'),
    ]

    source = models.ForeignKey(ExternalDataSource, on_delete=models.CASCADE)
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    external_id = models.CharField(max_length=200, help_text="ID from external system")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    # Sudan-specific crisis tracking
    crisis_date = models.DateField(help_text="Date relevant to Sudan crisis (from 2023-04-15)")
    report_date = models.DateField(help_text="Date when data was reported/published")

    # Geographic data
    admin_level = models.CharField(max_length=20, blank=True, help_text="Admin 0, 1, 2, etc.")
    location_name = models.CharField(max_length=200, blank=True)
    location_code = models.CharField(max_length=50, blank=True)

    # Data content
    raw_data = models.JSONField(help_text="Original JSON data from external API")
    processed_data = models.JSONField(null=True, blank=True, help_text="Processed/normalized data")

    # Metadata
    url = models.URLField(blank=True, help_text="Source URL")
    tags = models.JSONField(default=list, help_text="Tags for categorization")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_sudan_crisis_data'
        indexes = [
            models.Index(fields=['data_type', 'crisis_date']),
            models.Index(fields=['source', 'external_id']),
            models.Index(fields=['crisis_date']),
        ]
        unique_together = ['source', 'external_id']

    def __str__(self):
        return f"{self.get_data_type_display()} - {self.title[:50]}"


class DisplacementData(models.Model):
    """Specific model for IOM DTM displacement data"""
    crisis_data = models.ForeignKey(SudanCrisisData, on_delete=models.CASCADE)

    # Displacement metrics
    idp_individuals = models.PositiveIntegerField(null=True, blank=True)
    idp_families = models.PositiveIntegerField(null=True, blank=True)
    returnee_individuals = models.PositiveIntegerField(null=True, blank=True)
    returnee_families = models.PositiveIntegerField(null=True, blank=True)

    # Location details
    departure_location = models.CharField(max_length=200, blank=True)
    arrival_location = models.CharField(max_length=200, blank=True)

    # Site information
    site_type = models.CharField(max_length=100, blank=True)
    site_name = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'integrations_displacement_data'


class RefugeeData(models.Model):
    """Specific model for UNHCR refugee data"""
    crisis_data = models.ForeignKey(SudanCrisisData, on_delete=models.CASCADE)

    # Population figures
    refugees = models.PositiveIntegerField(null=True, blank=True)
    asylum_seekers = models.PositiveIntegerField(null=True, blank=True)
    returnees = models.PositiveIntegerField(null=True, blank=True)

    # Demographics
    country_of_origin = models.CharField(max_length=100, blank=True)
    country_of_asylum = models.CharField(max_length=100, blank=True)

    # Age/gender breakdown (stored as JSON for flexibility)
    demographics = models.JSONField(default=dict)

    class Meta:
        db_table = 'integrations_refugee_data'


class FundingData(models.Model):
    """Specific model for OCHA FTS funding data"""
    crisis_data = models.ForeignKey(SudanCrisisData, on_delete=models.CASCADE)

    # Funding amounts (in USD)
    requirements = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    funding_received = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    funding_gap = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Funding details
    donor_country = models.CharField(max_length=100, blank=True)
    recipient_organization = models.CharField(max_length=200, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    appeal_name = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = 'integrations_funding_data'


class HealthData(models.Model):
    """Specific model for WHO health crisis data"""
    crisis_data = models.ForeignKey(SudanCrisisData, on_delete=models.CASCADE)

    # Health indicators
    health_facilities_functional = models.PositiveIntegerField(null=True, blank=True)
    health_facilities_total = models.PositiveIntegerField(null=True, blank=True)

    # Disease outbreak data
    disease_name = models.CharField(max_length=100, blank=True)
    cases_reported = models.PositiveIntegerField(null=True, blank=True)
    deaths_reported = models.PositiveIntegerField(null=True, blank=True)

    # Population in need
    people_in_need_health = models.PositiveIntegerField(null=True, blank=True)
    people_reached_health = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'integrations_health_data'


class HumanitarianActionPlanData(models.Model):
    """Specific model for Humanitarian Action Info plan data"""
    crisis_data = models.ForeignKey(SudanCrisisData, on_delete=models.CASCADE)

    # Plan details
    plan_id = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=50, choices=[
        ('humanitarian_response_plan', 'Humanitarian Response Plan'),
        ('emergency_appeal', 'Emergency Appeal'),
        ('regional_response', 'Regional Response'),
        ('contingency_plan', 'Contingency Plan'),
        ('general_plan', 'General Plan'),
    ])

    # Funding information
    total_requirements_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    funded_amount_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    funding_gap_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    funding_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Target population
    target_population = models.CharField(max_length=200, blank=True)
    people_in_need = models.PositiveIntegerField(null=True, blank=True)

    # Timeline
    plan_start_date = models.DateField(null=True, blank=True)
    plan_end_date = models.DateField(null=True, blank=True)
    timeframe_description = models.CharField(max_length=200, blank=True)

    # Geographic and sector coverage
    sectors = models.JSONField(default=list, help_text="List of humanitarian sectors")
    locations = models.JSONField(default=list, help_text="List of affected locations")
    organizations = models.JSONField(default=list, help_text="List of participating organizations")

    # Objectives and activities
    objectives = models.JSONField(default=list, help_text="List of plan objectives")

    class Meta:
        db_table = 'integrations_humanitarian_action_plan_data'
        unique_together = ['crisis_data', 'plan_id']


class DataSyncLog(models.Model):
    """Log for tracking data synchronization activities"""
    source = models.ForeignKey(ExternalDataSource, on_delete=models.CASCADE)
    sync_start = models.DateTimeField()
    sync_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ])
    records_processed = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Sudan crisis specific filters
    date_from = models.DateField(default=get_crisis_start_date)
    date_to = models.DateField(default=get_current_date)

    class Meta:
        db_table = 'integrations_data_sync_log'
        ordering = ['-sync_start']

    def __str__(self):
        return f"{self.source.name} - {self.status} ({self.sync_start})"
