from rest_framework import serializers
from .models import (
    ExternalDataSource, SudanCrisisData, DisplacementData,
    RefugeeData, FundingData, HealthData, DataSyncLog
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