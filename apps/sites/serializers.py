from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point, GEOSGeometry
from .models import State, Locality, Site


class StateSerializer(serializers.ModelSerializer):
    localities_count = serializers.SerializerMethodField()
    sites_count = serializers.SerializerMethodField()
    
    class Meta:
        model = State
        fields = ['id', 'name', 'name_ar', 'boundary', 'localities_count', 'sites_count', 'created_at', 'updated_at']
    
    def get_localities_count(self, obj):
        return obj.localities.count()
    
    def get_sites_count(self, obj):
        return obj.sites.count()


class LocalitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    sites_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Locality
        fields = ['id', 'name', 'name_ar', 'state', 'state_name', 'boundary', 'sites_count', 'created_at', 'updated_at']
    
    def get_sites_count(self, obj):
        return obj.sites.count()


class SiteSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    locality_name = serializers.CharField(source='locality.name', read_only=True)
    coordinates = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    latitude = serializers.ReadOnlyField()
    
    class Meta:
        model = Site
        fields = [
            # Basic Information
            'id', 'name', 'name_ar', 'description', 'site_type', 'operational_status',
            'state', 'state_name', 'locality', 'locality_name', 
            
            # Location
            'location', 'coordinates', 'longitude', 'latitude', 'size_of_location',
            
            # Demographics
            'total_population', 'total_households',
            'children_under_18', 'adults_18_59', 'elderly_60_plus',
            'male_count', 'female_count',
            'disabled_count', 'pregnant_women', 'chronically_ill',
            
            # Reporting
            'report_date', 'reported_by',
            
            # Contact
            'contact_person', 'contact_phone', 'contact_email',
            
            # Timestamps
            'created_at', 'updated_at'
        ]


class SiteDetailSerializer(SiteSerializer):
    state_info = StateSerializer(source='state', read_only=True)
    locality_info = LocalitySerializer(source='locality', read_only=True)
    
    # Calculated demographic fields
    average_household_size = serializers.ReadOnlyField()
    vulnerability_rate = serializers.ReadOnlyField()
    child_dependency_ratio = serializers.ReadOnlyField()
    population_by_age_verified = serializers.ReadOnlyField()
    population_by_gender_verified = serializers.ReadOnlyField()
    
    class Meta(SiteSerializer.Meta):
        fields = SiteSerializer.Meta.fields + [
            'state_info', 'locality_info',
            'average_household_size', 'vulnerability_rate', 'child_dependency_ratio',
            'population_by_age_verified', 'population_by_gender_verified'
        ]


class SiteMapSerializer(serializers.ModelSerializer):
    coordinates = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    latitude = serializers.ReadOnlyField()
    state_name = serializers.CharField(source='state.name', read_only=True)
    locality_name = serializers.CharField(source='locality.name', read_only=True)
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_type', 'operational_status', 
            'coordinates', 'longitude', 'latitude', 'state_name', 'locality_name', 
            'total_population', 'total_households', 'size_of_location'
        ]


class SiteProfileSerializer(serializers.ModelSerializer):
    """Comprehensive site profile serializer with all demographic data"""
    state_name = serializers.CharField(source='state.name', read_only=True)
    locality_name = serializers.CharField(source='locality.name', read_only=True)
    coordinates = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    latitude = serializers.ReadOnlyField()
    
    # Calculated fields
    average_household_size = serializers.ReadOnlyField()
    vulnerability_rate = serializers.ReadOnlyField()
    child_dependency_ratio = serializers.ReadOnlyField()
    population_by_age_verified = serializers.ReadOnlyField()
    population_by_gender_verified = serializers.ReadOnlyField()
    
    class Meta:
        model = Site
        fields = [
            # Basic Information
            'id', 'name', 'name_ar', 'description', 'site_type', 'operational_status',
            'state', 'state_name', 'locality', 'locality_name',
            
            # Location
            'coordinates', 'longitude', 'latitude', 'size_of_location',
            
            # Population Demographics
            'total_population', 'total_households',
            
            # Age Demographics
            'children_under_18', 'adults_18_59', 'elderly_60_plus',
            
            # Gender Demographics  
            'male_count', 'female_count',
            
            # Vulnerability Demographics
            'disabled_count', 'pregnant_women', 'chronically_ill',
            
            # Calculated Demographics
            'average_household_size', 'vulnerability_rate', 'child_dependency_ratio',
            'population_by_age_verified', 'population_by_gender_verified',
            
            # Reporting
            'report_date', 'reported_by',
            
            # Contact
            'contact_person', 'contact_phone', 'contact_email',
            
            # Timestamps
            'created_at', 'updated_at'
        ]


# GeoJSON Serializers for advanced GIS functionality
class StateGeoSerializer(GeoFeatureModelSerializer):
    localities_count = serializers.SerializerMethodField()
    sites_count = serializers.SerializerMethodField()
    
    class Meta:
        model = State
        geo_field = 'center_point'
        fields = ['id', 'name', 'name_ar', 'localities_count', 'sites_count', 'created_at', 'updated_at']
    
    def get_localities_count(self, obj):
        return obj.localities.count()
    
    def get_sites_count(self, obj):
        return obj.sites.count()


class LocalityGeoSerializer(GeoFeatureModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    sites_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Locality
        geo_field = 'center_point'
        fields = ['id', 'name', 'name_ar', 'state', 'state_name', 'sites_count', 'created_at', 'updated_at']
    
    def get_sites_count(self, obj):
        return obj.sites.count()


class SiteGeoSerializer(GeoFeatureModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    locality_name = serializers.CharField(source='locality.name', read_only=True)
    
    class Meta:
        model = Site
        geo_field = 'location'
        fields = [
            'id', 'name', 'name_ar', 'description', 'site_type', 'operational_status',
            'state', 'state_name', 'locality', 'locality_name',
            'population', 'families', 'vulnerable_population',
            'contact_person', 'contact_phone', 'contact_email',
            'created_at', 'updated_at'
        ]