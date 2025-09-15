from rest_framework import serializers
from .models import Assessment, AssessmentResponse, KoboIntegrationSettings
from apps.sites.models import Site
from apps.accounts.models import User


class AssessmentSerializer(serializers.ModelSerializer):
    target_sites = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Site.objects.all(),
        required=False
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )
    created_by = serializers.StringRelatedField(read_only=True)
    response_count = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'title_ar', 'description', 'assessment_type', 'status',
            'kobo_form_id', 'kobo_form_url', 'kobo_username',
            'target_sites', 'created_by', 'assigned_to',
            'start_date', 'end_date', 'response_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        target_sites = validated_data.pop('target_sites', [])
        assigned_to = validated_data.pop('assigned_to', [])
        
        assessment = Assessment.objects.create(**validated_data)
        
        if target_sites:
            assessment.target_sites.set(target_sites)
        if assigned_to:
            assessment.assigned_to.set(assigned_to)
            
        return assessment


class AssessmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing assessments"""
    response_count = serializers.ReadOnlyField()
    site_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'assessment_type', 'status',
            'start_date', 'end_date', 'response_count', 'site_count',
            'created_at'
        ]
    
    def get_site_count(self, obj):
        return obj.target_sites.count()


class AssessmentResponseSerializer(serializers.ModelSerializer):
    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())
    site = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all())
    respondent = serializers.StringRelatedField(read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    
    class Meta:
        model = AssessmentResponse
        fields = [
            'id', 'assessment', 'assessment_title', 'site', 'site_name',
            'respondent', 'kobo_submission_id', 'kobo_data',
            'is_submitted', 'submitted_at', 'gps_location',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['respondent', 'created_at', 'updated_at']


class KoboIntegrationSettingsSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = KoboIntegrationSettings
        fields = [
            'id', 'user', 'kobo_server_url', 'kobo_username', 
            'kobo_api_token', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
        extra_kwargs = {
            'kobo_api_token': {'write_only': True}
        }


class KoboFormSerializer(serializers.Serializer):
    """Serializer for Kobo form data"""
    uid = serializers.CharField()
    name = serializers.CharField()
    asset_type = serializers.CharField()
    date_created = serializers.DateTimeField()
    date_modified = serializers.DateTimeField()
    deployment_status = serializers.CharField()
    submissions_count = serializers.IntegerField(default=0)
    url = serializers.URLField(required=False)


class AssessmentLaunchSerializer(serializers.Serializer):
    """Serializer for launching assessment"""
    assessment_id = serializers.IntegerField()
    site_id = serializers.IntegerField(required=False)
    launch_url = serializers.URLField(read_only=True)
    message = serializers.CharField(read_only=True)