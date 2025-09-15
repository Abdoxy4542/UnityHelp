from django.db import models
from django.conf import settings
from apps.sites.models import Site


class Assessment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    ASSESSMENT_TYPES = [
        ('rapid', 'Rapid Assessment'),
        ('detailed', 'Detailed Assessment'),
        ('needs', 'Needs Assessment'),
        ('monitoring', 'Monitoring & Evaluation'),
        ('baseline', 'Baseline Assessment'),
    ]
    
    title = models.CharField(max_length=255, help_text="Assessment title")
    title_ar = models.CharField(max_length=255, blank=True, help_text="Assessment title in Arabic")
    description = models.TextField(blank=True, help_text="Assessment description")
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='rapid')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Kobo Integration
    kobo_form_id = models.CharField(max_length=255, blank=True, help_text="Kobo form asset ID")
    kobo_form_url = models.URLField(blank=True, help_text="Direct link to Kobo form")
    kobo_username = models.CharField(max_length=255, blank=True, help_text="Kobo username for API access")
    
    # Site association
    target_sites = models.ManyToManyField(Site, related_name='assessments', blank=True, help_text="Sites where this assessment should be conducted")
    
    # Meta information
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assessments')
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_assessments', blank=True, help_text="Users assigned to conduct this assessment")
    
    # Timing
    start_date = models.DateField(null=True, blank=True, help_text="Assessment start date")
    end_date = models.DateField(null=True, blank=True, help_text="Assessment end date")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def response_count(self):
        return self.responses.count()


class AssessmentResponse(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='responses')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='assessment_responses')
    respondent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_responses')
    
    # Kobo data
    kobo_submission_id = models.CharField(max_length=255, blank=True, help_text="Kobo submission UUID")
    kobo_data = models.JSONField(null=True, blank=True, help_text="Raw Kobo submission data")
    
    # Status tracking
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # GPS location from mobile device
    gps_location = models.JSONField(null=True, blank=True, help_text="GPS coordinates from mobile device")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['assessment', 'site', 'respondent']
    
    def __str__(self):
        return f"{self.assessment.title} - {self.site.name} by {self.respondent.username}"


class KoboIntegrationSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kobo_settings')
    kobo_server_url = models.URLField(default='https://kf.kobotoolbox.org', help_text="Kobo server URL")
    kobo_username = models.CharField(max_length=255, help_text="Kobo username")
    kobo_api_token = models.CharField(max_length=255, help_text="Kobo API token")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Kobo settings for {self.user.username}"
