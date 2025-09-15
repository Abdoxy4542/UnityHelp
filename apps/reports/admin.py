from django.contrib import admin
from django.utils.html import format_html
from .models import FieldReport, ReportAnalysis, ReportTag, ReportTagging


@admin.register(ReportTag)
class ReportTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_ar', 'colored_badge', 'report_count', 'created_at']
    search_fields = ['name', 'name_ar']
    list_filter = ['created_at']
    
    def colored_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.color, obj.name
        )
    colored_badge.short_description = 'Badge'
    
    def report_count(self, obj):
        return obj.reports.count()
    report_count.short_description = 'Reports'


class ReportTaggingInline(admin.TabularInline):
    model = ReportTagging
    extra = 0
    fields = ['tag', 'confidence', 'auto_generated']


class ReportAnalysisInline(admin.StackedInline):
    model = ReportAnalysis
    extra = 0
    fields = ['analysis_type', 'ai_confidence', 'analysis_data', 'key_insights']
    readonly_fields = ['created_at']


@admin.register(FieldReport)
class FieldReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'site', 'reporter', 'report_type', 'priority', 'status', 'has_media', 'created_at']
    list_filter = ['report_type', 'priority', 'status', 'site__state', 'created_at']
    search_fields = ['title', 'text_content', 'site__name', 'reporter__username']
    readonly_fields = ['created_at', 'updated_at', 'processed_at', 'verified_at', 'is_processed']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'site', 'reporter', 'report_type', 'priority')
        }),
        ('Content', {
            'fields': ('text_content', 'voice_file', 'image_file', 'location_coordinates')
        }),
        ('Processing', {
            'fields': ('status', 'ai_analysis', 'verified_by', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at', 'verified_at', 'is_processed'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ReportAnalysisInline, ReportTaggingInline]
    
    def has_media(self, obj):
        return obj.has_media
    has_media.boolean = True
    has_media.short_description = 'Media'
    
    actions = ['mark_as_processing', 'mark_as_processed']
    
    def mark_as_processing(self, request, queryset):
        count = queryset.update(status='processing')
        self.message_user(request, f'{count} reports marked as processing.')
    mark_as_processing.short_description = 'Mark selected reports as processing'
    
    def mark_as_processed(self, request, queryset):
        count = queryset.update(status='processed')
        self.message_user(request, f'{count} reports marked as processed.')
    mark_as_processed.short_description = 'Mark selected reports as processed'


@admin.register(ReportAnalysis)
class ReportAnalysisAdmin(admin.ModelAdmin):
    list_display = ['report', 'analysis_type', 'ai_confidence', 'model_version', 'processing_time', 'created_at']
    list_filter = ['analysis_type', 'model_version', 'created_at']
    search_fields = ['report__title', 'analysis_type']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('report', 'analysis_type', 'ai_confidence', 'model_version', 'processing_time')
        }),
        ('Results', {
            'fields': ('analysis_data', 'extracted_entities', 'key_insights')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
