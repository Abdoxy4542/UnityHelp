from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class FieldReport(models.Model):
    REPORT_TYPES = [
        ('text', _('Text Report')),
        ('voice', _('Voice Report')),
        ('image', _('Image Report')),
        ('mixed', _('Mixed Media Report')),
    ]
    
    PRIORITY_LEVELS = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('processing', _('AI Processing')),
        ('processed', _('Processed')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
    ]

    # Core Information
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='field_reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='text')
    
    # Report Content
    title = models.CharField(max_length=255, help_text="Brief report title")
    text_content = models.TextField(blank=True, help_text="Text content of the report")
    voice_file = models.FileField(
        upload_to='reports/voice/%Y/%m/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg', 'm4a'])],
        help_text="Voice recording (MP3, WAV, OGG, M4A)"
    )
    image_file = models.ImageField(
        upload_to='reports/images/%Y/%m/',
        blank=True,
        help_text="Supporting image"
    )
    
    # Metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    location_coordinates = models.JSONField(null=True, blank=True, help_text="GPS coordinates where report was made")
    
    # Processing Information
    ai_analysis = models.JSONField(null=True, blank=True, help_text="AI analysis results")
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_reports'
    )
    verification_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Field Report')
        verbose_name_plural = _('Field Reports')

    def __str__(self):
        return f"{self.title} - {self.site.name} ({self.get_report_type_display()})"
    
    @property
    def has_media(self):
        return bool(self.voice_file or self.image_file)
    
    @property
    def is_processed(self):
        return self.status in ['processed', 'verified']


class ReportAnalysis(models.Model):
    ANALYSIS_TYPES = [
        ('demographic', _('Demographic Analysis')),
        ('needs_assessment', _('Needs Assessment')),
        ('risk_assessment', _('Risk Assessment')),
        ('resource_gap', _('Resource Gap Analysis')),
        ('sentiment', _('Sentiment Analysis')),
    ]

    report = models.ForeignKey(FieldReport, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    
    # Analysis Results
    ai_confidence = models.FloatField(help_text="AI confidence score (0-1)")
    analysis_data = models.JSONField(help_text="Structured analysis results")
    extracted_entities = models.JSONField(null=True, blank=True, help_text="Named entities, numbers, locations")
    key_insights = models.JSONField(null=True, blank=True, help_text="Key insights and recommendations")
    
    # Metadata
    model_version = models.CharField(max_length=50, help_text="AI model version used")
    processing_time = models.FloatField(help_text="Processing time in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['report', 'analysis_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report.title} - {self.get_analysis_type_display()}"


class ReportTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    name_ar = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ReportTagging(models.Model):
    report = models.ForeignKey(FieldReport, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(ReportTag, on_delete=models.CASCADE, related_name='reports')
    confidence = models.FloatField(default=1.0, help_text="Tagging confidence (0-1)")
    auto_generated = models.BooleanField(default=False, help_text="Auto-generated by AI")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['report', 'tag']
