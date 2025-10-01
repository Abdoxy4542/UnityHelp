from rest_framework import serializers
from .models import (
    ExternalDataSource, SudanCrisisData, DisplacementData,
    RefugeeData, FundingData, HealthData, DataSyncLog,
    HumanitarianActionPlanData
)


class ExternalDataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalDataSource
        fields = '__all__'


class SudanCrisisDataSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)
    platform = serializers.CharField(source='source.platform', read_only=True)

    class Meta:
        model = SudanCrisisData
        fields = [
            'id', 'source', 'source_name', 'platform', 'data_type', 'external_id',
            'title', 'description', 'crisis_date', 'report_date', 'admin_level',
            'location_name', 'location_code', 'url', 'tags', 'created_at', 'updated_at'
        ]


class DisplacementDataSerializer(serializers.ModelSerializer):
    crisis_info = SudanCrisisDataSerializer(source='crisis_data', read_only=True)

    class Meta:
        model = DisplacementData
        fields = '__all__'


class RefugeeDataSerializer(serializers.ModelSerializer):
    crisis_info = SudanCrisisDataSerializer(source='crisis_data', read_only=True)

    class Meta:
        model = RefugeeData
        fields = '__all__'


class FundingDataSerializer(serializers.ModelSerializer):
    crisis_info = SudanCrisisDataSerializer(source='crisis_data', read_only=True)

    class Meta:
        model = FundingData
        fields = '__all__'


class HealthDataSerializer(serializers.ModelSerializer):
    crisis_info = SudanCrisisDataSerializer(source='crisis_data', read_only=True)

    class Meta:
        model = HealthData
        fields = '__all__'


class DataSyncLogSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)
    platform = serializers.CharField(source='source.platform', read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = DataSyncLog
        fields = [
            'id', 'source', 'source_name', 'platform', 'sync_start', 'sync_end',
            'status', 'records_processed', 'records_created', 'records_updated',
            'error_message', 'date_from', 'date_to', 'duration_seconds'
        ]

    def get_duration_seconds(self, obj):
        if obj.sync_start and obj.sync_end:
            return (obj.sync_end - obj.sync_start).total_seconds()
        return None


class HumanitarianActionPlanDataSerializer(serializers.ModelSerializer):
    crisis_info = SudanCrisisDataSerializer(source='crisis_data', read_only=True)
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    funding_gap_calculated = serializers.SerializerMethodField()
    sector_count = serializers.SerializerMethodField()
    location_count = serializers.SerializerMethodField()
    organization_count = serializers.SerializerMethodField()

    class Meta:
        model = HumanitarianActionPlanData
        fields = [
            'id', 'crisis_data', 'crisis_info', 'plan_id', 'plan_type', 'plan_type_display',
            'total_requirements_usd', 'funded_amount_usd', 'funding_gap_usd', 'funding_percentage',
            'funding_gap_calculated', 'target_population', 'people_in_need',
            'plan_start_date', 'plan_end_date', 'timeframe_description',
            'sectors', 'sector_count', 'locations', 'location_count',
            'organizations', 'organization_count', 'objectives'
        ]

    def get_funding_gap_calculated(self, obj):
        """Calculate funding gap if not explicitly set"""
        if obj.funding_gap_usd:
            return float(obj.funding_gap_usd)
        elif obj.total_requirements_usd and obj.funded_amount_usd:
            return float(obj.total_requirements_usd - obj.funded_amount_usd)
        return None

    def get_sector_count(self, obj):
        """Return count of sectors covered by this plan"""
        return len(obj.sectors) if obj.sectors else 0

    def get_location_count(self, obj):
        """Return count of locations covered by this plan"""
        return len(obj.locations) if obj.locations else 0

    def get_organization_count(self, obj):
        """Return count of organizations involved in this plan"""
        return len(obj.organizations) if obj.organizations else 0