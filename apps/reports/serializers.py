from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import FieldReport, ReportAnalysis, ReportTag, ReportTagging

User = get_user_model()


class ReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class ReportTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTag
        fields = ['id', 'name', 'name_ar', 'color']


class ReportTaggingSerializer(serializers.ModelSerializer):
    tag = ReportTagSerializer(read_only=True)
    
    class Meta:
        model = ReportTagging
        fields = ['tag', 'confidence', 'auto_generated']


class ReportAnalysisSerializer(serializers.ModelSerializer):
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    
    class Meta:
        model = ReportAnalysis
        fields = [
            'id', 'analysis_type', 'analysis_type_display', 'ai_confidence',
            'analysis_data', 'extracted_entities', 'key_insights',
            'model_version', 'processing_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FieldReportListSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer(read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    site_id = serializers.IntegerField(source='site.id', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_media = serializers.ReadOnlyField()
    tags = ReportTaggingSerializer(many=True, read_only=True)
    
    class Meta:
        model = FieldReport
        fields = [
            'id', 'title', 'report_type', 'report_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'site_id', 'site_name', 'reporter', 'has_media',
            'location_coordinates', 'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FieldReportDetailSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer(read_only=True)
    verified_by = ReporterSerializer(read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    site_id = serializers.IntegerField(source='site.id', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_media = serializers.ReadOnlyField()
    is_processed = serializers.ReadOnlyField()
    analyses = ReportAnalysisSerializer(many=True, read_only=True)
    tags = ReportTaggingSerializer(many=True, read_only=True)
    
    class Meta:
        model = FieldReport
        fields = [
            'id', 'title', 'text_content', 'report_type', 'report_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'site_id', 'site_name', 'reporter', 'verified_by',
            'voice_file', 'image_file', 'has_media', 'is_processed',
            'location_coordinates', 'ai_analysis', 'verification_notes',
            'analyses', 'tags', 'created_at', 'updated_at', 
            'processed_at', 'verified_at'
        ]
        read_only_fields = [
            'id', 'reporter', 'verified_by', 'ai_analysis', 
            'processed_at', 'verified_at', 'created_at', 'updated_at'
        ]


class FieldReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldReport
        fields = [
            'site', 'title', 'text_content', 'report_type',
            'priority', 'voice_file', 'image_file', 'location_coordinates'
        ]
    
    def validate(self, data):
        report_type = data.get('report_type')
        text_content = data.get('text_content')
        voice_file = data.get('voice_file')
        image_file = data.get('image_file')
        
        if report_type == 'text' and not text_content:
            raise serializers.ValidationError("Text content is required for text reports.")
        
        if report_type == 'voice' and not voice_file:
            raise serializers.ValidationError("Voice file is required for voice reports.")
        
        if report_type == 'image' and not image_file:
            raise serializers.ValidationError("Image file is required for image reports.")
        
        if report_type == 'mixed' and not any([text_content, voice_file, image_file]):
            raise serializers.ValidationError("At least one content type is required for mixed reports.")
        
        return data
    
    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class FieldReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldReport
        fields = [
            'title', 'text_content', 'priority', 'status',
            'verification_notes', 'location_coordinates'
        ]
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        # Handle status updates
        new_status = validated_data.get('status')
        if new_status and new_status != instance.status:
            if new_status == 'verified':
                validated_data['verified_by'] = user
                validated_data['verified_at'] = timezone.now()
        
        return super().update(instance, validated_data)