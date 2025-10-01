from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
import secrets

from apps.accounts.models import User, UserProfile
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse, KoboIntegrationSettings
from apps.reports.models import FieldReport, ReportAnalysis, ReportTag
from ..models import MobileDevice, RefreshToken, SyncLog


# ================== Authentication Serializers ==================

class MobileDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileDevice
        fields = ['id', 'device_id', 'platform', 'fcm_token', 'app_version', 'os_version', 'device_model']
        read_only_fields = ['id']


class MobileUserSerializer(serializers.ModelSerializer):
    """Optimized user serializer for mobile apps"""
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    assigned_sites_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'organization', 'phone_number', 'location', 'preferred_language',
            'is_verified', 'avatar_url', 'assigned_sites_count', 'date_joined'
        ]
        read_only_fields = ['id', 'username', 'date_joined']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_avatar_url(self, obj):
        try:
            if obj.profile.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.profile.avatar.url)
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return None

    def get_assigned_sites_count(self, obj):
        return obj.assigned_sites.count()


class MobileLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField()
    platform = serializers.ChoiceField(choices=MobileDevice.PLATFORM_CHOICES)
    fcm_token = serializers.CharField(required=False, allow_blank=True)
    app_version = serializers.CharField(required=False, allow_blank=True)
    os_version = serializers.CharField(required=False, allow_blank=True)
    device_model = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(username=user.username, password=password)
            if user is None:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_verified:
                raise serializers.ValidationError('Email not verified')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials')

        attrs['user'] = user
        return attrs


class MobileRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    device_id = serializers.CharField(write_only=True)
    platform = serializers.ChoiceField(choices=MobileDevice.PLATFORM_CHOICES, write_only=True)
    fcm_token = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'organization', 'phone_number',
            'preferred_language', 'password', 'password_confirm', 'device_id',
            'platform', 'fcm_token'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists")

        return attrs

    def create(self, validated_data):
        # Remove device-specific data
        device_data = {
            'device_id': validated_data.pop('device_id'),
            'platform': validated_data.pop('platform'),
            'fcm_token': validated_data.pop('fcm_token', ''),
        }
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Generate username from email
        email = validated_data['email']
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            **validated_data
        )

        # Create profile
        UserProfile.objects.create(user=user)

        # Store device data for later registration
        user._device_data = device_data
        return user


# ================== Site Serializers ==================

class MobileStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name', 'name_ar', 'center_point']


class MobileLocalitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)

    class Meta:
        model = Locality
        fields = ['id', 'name', 'name_ar', 'state', 'state_name', 'center_point']


class MobileSiteSerializer(serializers.ModelSerializer):
    """Mobile-optimized site serializer"""
    state_name = serializers.CharField(source='state.name', read_only=True)
    locality_name = serializers.CharField(source='locality.name', read_only=True)
    coordinates = serializers.SerializerMethodField()
    population_summary = serializers.SerializerMethodField()
    last_updated = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'name_ar', 'description', 'site_type', 'operational_status',
            'state', 'state_name', 'locality', 'locality_name', 'location', 'coordinates',
            'total_population', 'total_households', 'population_summary',
            'contact_person', 'contact_phone', 'contact_email', 'last_updated'
        ]

    def get_coordinates(self, obj):
        return obj.coordinates

    def get_population_summary(self, obj):
        return {
            'total_population': obj.total_population or 0,
            'total_households': obj.total_households or 0,
            'children_under_18': obj.children_under_18 or 0,
            'adults_18_59': obj.adults_18_59 or 0,
            'elderly_60_plus': obj.elderly_60_plus or 0,
            'male_count': obj.male_count or 0,
            'female_count': obj.female_count or 0,
            'vulnerable_count': (obj.disabled_count or 0) + (obj.pregnant_women or 0) + (obj.chronically_ill or 0)
        }


class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating sites via mobile"""

    class Meta:
        model = Site
        fields = [
            'name', 'name_ar', 'description', 'site_type', 'operational_status',
            'state', 'locality', 'location', 'size_of_location',
            'total_population', 'total_households',
            'children_under_18', 'adults_18_59', 'elderly_60_plus',
            'male_count', 'female_count',
            'disabled_count', 'pregnant_women', 'chronically_ill',
            'contact_person', 'contact_phone', 'contact_email',
            'report_date', 'reported_by'
        ]

    def validate_location(self, value):
        """Validate GeoJSON location format"""
        if value and isinstance(value, dict):
            if value.get('type') != 'Point':
                raise serializers.ValidationError("Location must be a Point type")
            coordinates = value.get('coordinates', [])
            if len(coordinates) != 2:
                raise serializers.ValidationError("Coordinates must contain [longitude, latitude]")
            try:
                lon, lat = float(coordinates[0]), float(coordinates[1])
                if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                    raise serializers.ValidationError("Invalid coordinates range")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Coordinates must be valid numbers")
        return value


# ================== Assessment Serializers ==================

class MobileAssessmentSerializer(serializers.ModelSerializer):
    """Mobile-optimized assessment serializer"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    target_sites_count = serializers.SerializerMethodField()
    assigned_to_me = serializers.SerializerMethodField()
    response_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'title_ar', 'description', 'assessment_type', 'status',
            'kobo_form_id', 'kobo_form_url', 'start_date', 'end_date',
            'created_by', 'created_by_name', 'target_sites_count', 'assigned_to_me',
            'response_count', 'created_at', 'updated_at'
        ]

    def get_target_sites_count(self, obj):
        return obj.target_sites.count()

    def get_assigned_to_me(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.assigned_to.filter(id=request.user.id).exists()
        return False


class MobileAssessmentResponseSerializer(serializers.ModelSerializer):
    """Mobile assessment response serializer"""
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    respondent_name = serializers.CharField(source='respondent.get_full_name', read_only=True)

    class Meta:
        model = AssessmentResponse
        fields = [
            'id', 'assessment', 'assessment_title', 'site', 'site_name',
            'respondent', 'respondent_name', 'kobo_submission_id', 'kobo_data',
            'is_submitted', 'submitted_at', 'gps_location',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'respondent', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['respondent'] = self.context['request'].user
        return super().create(validated_data)


# ================== Sync Serializers ==================

class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = [
            'id', 'sync_type', 'status', 'total_items', 'processed_items',
            'failed_items', 'progress_percentage', 'error_message',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'progress_percentage']


class InitialSyncRequestSerializer(serializers.Serializer):
    """Request data for initial sync"""
    last_sync_date = serializers.DateTimeField(required=False, allow_null=True)
    data_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['sites', 'assessments', 'field_reports']
    )


class BulkUploadSerializer(serializers.Serializer):
    """Serializer for bulk data upload from mobile"""
    data_type = serializers.CharField()
    items = serializers.ListField(child=serializers.DictField())

    def validate_data_type(self, value):
        allowed_types = ['sites', 'assessment_responses', 'field_reports']
        if value not in allowed_types:
            raise serializers.ValidationError(f"Data type must be one of: {allowed_types}")
        return value


# ================== Health Check Serializer ==================

class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    services = serializers.DictField()


# ================== Reports Serializers (Mobile Optimized) ==================

class MobileFieldReportListSerializer(serializers.ModelSerializer):
    """Mobile-optimized list serializer for field reports"""
    reporter_name = serializers.CharField(source='reporter.get_full_name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_media = serializers.ReadOnlyField()

    class Meta:
        model = FieldReport
        fields = [
            'id', 'title', 'report_type', 'report_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'site_name', 'reporter_name', 'has_media',
            'location_coordinates', 'created_at'
        ]


class MobileFieldReportDetailSerializer(serializers.ModelSerializer):
    """Mobile-optimized detail serializer for field reports"""
    reporter_name = serializers.CharField(source='reporter.get_full_name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_media = serializers.ReadOnlyField()
    is_processed = serializers.ReadOnlyField()

    # Mobile-friendly file URLs
    voice_file_url = serializers.SerializerMethodField()
    image_file_url = serializers.SerializerMethodField()

    class Meta:
        model = FieldReport
        fields = [
            'id', 'title', 'text_content', 'report_type', 'report_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'site_name', 'reporter_name', 'has_media', 'is_processed',
            'voice_file_url', 'image_file_url', 'location_coordinates',
            'verification_notes', 'created_at', 'updated_at'
        ]

    def get_voice_file_url(self, obj):
        if obj.voice_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.voice_file.url)
        return None

    def get_image_file_url(self, obj):
        if obj.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_file.url)
        return None


class MobileFieldReportCreateSerializer(serializers.ModelSerializer):
    """Mobile-optimized create serializer for field reports"""

    class Meta:
        model = FieldReport
        fields = [
            'site', 'title', 'text_content', 'report_type',
            'priority', 'voice_file', 'image_file', 'location_coordinates'
        ]

    def validate(self, data):
        """Validate report data based on type"""
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

        # Validate site assignment for user
        site = data.get('site')
        user = self.context['request'].user

        # Check if user has access to the site
        if hasattr(user, 'role'):
            if user.role == 'gso':
                # GSOs can only submit reports for their assigned sites
                if hasattr(user, 'managed_sites') and site not in user.managed_sites.all():
                    raise serializers.ValidationError("You can only submit reports for your assigned sites.")
            elif user.role in ['ngo_user', 'public_user']:
                # Regular users can submit reports for sites in their organization
                if hasattr(user, 'organization') and site.organization != user.organization:
                    raise serializers.ValidationError("You can only submit reports for sites in your organization.")

        return data

    def create(self, validated_data):
        """Create report with current user as reporter"""
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class MobileFieldReportUpdateSerializer(serializers.ModelSerializer):
    """Mobile-optimized update serializer for field reports"""

    class Meta:
        model = FieldReport
        fields = [
            'title', 'text_content', 'priority', 'location_coordinates'
        ]

    def update(self, instance, validated_data):
        """Update report with restrictions"""
        user = self.context['request'].user

        # Only allow updates by the reporter or authorized users
        if instance.reporter != user and not user.is_staff:
            if hasattr(user, 'role') and user.role not in ['admin', 'cluster_lead']:
                raise serializers.ValidationError("You can only update your own reports.")

        # Don't allow updates to processed/verified reports
        if instance.status in ['verified', 'rejected']:
            raise serializers.ValidationError("Cannot update verified or rejected reports.")

        return super().update(instance, validated_data)