from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import date, datetime, timedelta
from .models import (
    ExternalDataSource, SudanCrisisData, DisplacementData,
    RefugeeData, FundingData, HealthData, DataSyncLog
)
from .serializers import (
    SudanCrisisDataSerializer, ExternalDataSourceSerializer,
    DataSyncLogSerializer
)
from .hdx_service import get_hdx_service, get_hdx_hapi_service
from .dtm_service import get_dtm_service
from .unhcr_service import get_unhcr_service
from .fts_service import get_fts_service
import logging

logger = logging.getLogger(__name__)


class SudanCrisisDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for accessing Sudan crisis data from external sources"""
    permission_classes = [IsAuthenticated]
    queryset = SudanCrisisData.objects.all()
    serializer_class = SudanCrisisDataSerializer

    def get_queryset(self):
        queryset = SudanCrisisData.objects.all()

        # Filter by data type
        data_type = self.request.query_params.get('data_type')
        if data_type:
            queryset = queryset.filter(data_type=data_type)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if from_date:
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                queryset = queryset.filter(crisis_date__gte=from_date)
            except ValueError:
                pass

        if to_date:
            try:
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                queryset = queryset.filter(crisis_date__lte=to_date)
            except ValueError:
                pass

        # Filter by source platform
        platform = self.request.query_params.get('platform')
        if platform:
            queryset = queryset.filter(source__platform=platform)

        return queryset.order_by('-crisis_date')

    @action(detail=False, methods=['get'])
    def crisis_timeline(self, request):
        """Get crisis data timeline since April 15, 2023"""
        crisis_start = date(2023, 4, 15)
        end_date = date.today()

        # Group data by month
        monthly_data = {}

        queryset = self.get_queryset().filter(
            crisis_date__gte=crisis_start,
            crisis_date__lte=end_date
        )

        for item in queryset:
            month_key = item.crisis_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'displacement': 0,
                    'funding': 0,
                    'health_incidents': 0,
                    'total_records': 0
                }

            monthly_data[month_key]['total_records'] += 1

            if item.data_type == 'displacement':
                displacement_data = DisplacementData.objects.filter(crisis_data=item).first()
                if displacement_data and displacement_data.idp_individuals:
                    monthly_data[month_key]['displacement'] += displacement_data.idp_individuals

            elif item.data_type == 'funding':
                funding_data = FundingData.objects.filter(crisis_data=item).first()
                if funding_data and funding_data.funding_received:
                    monthly_data[month_key]['funding'] += float(funding_data.funding_received)

            elif item.data_type == 'health':
                monthly_data[month_key]['health_incidents'] += 1

        timeline = list(monthly_data.values())
        timeline.sort(key=lambda x: x['month'])

        return Response({
            'timeline': timeline,
            'total_months': len(timeline),
            'crisis_start_date': crisis_start.isoformat(),
            'last_updated': timezone.now().isoformat()
        })

    @action(detail=False, methods=['get'])
    def summary_statistics(self, request):
        """Get summary statistics for Sudan crisis data"""
        crisis_start = date(2023, 4, 15)

        queryset = self.get_queryset().filter(crisis_date__gte=crisis_start)

        # Count by data type
        data_type_counts = {}
        for choice in SudanCrisisData.DATA_TYPE_CHOICES:
            count = queryset.filter(data_type=choice[0]).count()
            data_type_counts[choice[1]] = count

        # Latest displacement figures
        latest_displacement = DisplacementData.objects.filter(
            crisis_data__crisis_date__gte=crisis_start
        ).order_by('-crisis_data__crisis_date').first()

        # Total funding figures
        from django.db import models
        total_funding = FundingData.objects.filter(
            crisis_data__crisis_date__gte=crisis_start
        ).aggregate(
            total_received=models.Sum('funding_received'),
            total_requirements=models.Sum('requirements')
        )

        return Response({
            'crisis_duration_days': (date.today() - crisis_start).days,
            'total_data_records': queryset.count(),
            'data_by_type': data_type_counts,
            'latest_displacement': {
                'idp_individuals': latest_displacement.idp_individuals if latest_displacement else 0,
                'idp_families': latest_displacement.idp_families if latest_displacement else 0,
                'last_updated': latest_displacement.crisis_data.crisis_date.isoformat() if latest_displacement else None
            },
            'funding_summary': {
                'total_received_usd': float(total_funding['total_received'] or 0),
                'total_requirements_usd': float(total_funding['total_requirements'] or 0),
                'funding_gap_usd': float((total_funding['total_requirements'] or 0) - (total_funding['total_received'] or 0))
            },
            'last_updated': timezone.now().isoformat()
        })


class DataIntegrationViewSet(viewsets.ViewSet):
    """ViewSet for managing data integration with external humanitarian platforms"""
    permission_classes = [AllowAny]  # Temporarily allow any for testing

    @action(detail=False, methods=['post'])
    def sync_hdx_data(self, request):
        """Trigger HDX data synchronization for Sudan crisis"""
        try:
            from_date = request.data.get('from_date', '2023-04-15')
            to_date = request.data.get('to_date', date.today().isoformat())

            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

            # Get or create HDX data source
            hdx_source, created = ExternalDataSource.objects.get_or_create(
                platform='hdx',
                name='HDX Sudan Crisis Data',
                defaults={
                    'api_endpoint': 'https://hapi.humdata.org/api/v1',
                    'is_active': True
                }
            )

            # Start sync log
            sync_log = DataSyncLog.objects.create(
                source=hdx_source,
                sync_start=timezone.now(),
                status='running',
                date_from=from_date,
                date_to=to_date
            )

            try:
                # Use HDX HAPI service to get comprehensive data
                hapi_service = get_hdx_hapi_service()

                sudan_data = hapi_service.get_all_sudan_crisis_data(
                    from_date=from_date,
                    to_date=to_date
                )

                records_created = 0

                # Process each data type
                for data_type, records in sudan_data.items():
                    for record in records:
                        # Create SudanCrisisData record
                        crisis_data, created = SudanCrisisData.objects.get_or_create(
                            source=hdx_source,
                            external_id=str(record.get('id', f"{data_type}_{records_created}")),
                            defaults={
                                'data_type': self._map_hdx_data_type(data_type),
                                'title': f"HDX {data_type.title()} Data",
                                'description': f"Sudan {data_type} data from HDX HAPI",
                                'crisis_date': from_date,
                                'report_date': date.today(),
                                'location_name': record.get('location_name', 'Sudan'),
                                'raw_data': record,
                                'url': f"https://hapi.humdata.org/api/v1/{data_type}"
                            }
                        )

                        if created:
                            records_created += 1

                # Update sync log
                sync_log.sync_end = timezone.now()
                sync_log.status = 'completed'
                sync_log.records_processed = sum(len(records) for records in sudan_data.values())
                sync_log.records_created = records_created
                sync_log.save()

                # Update source last sync
                hdx_source.last_sync = timezone.now()
                hdx_source.save()

                return Response({
                    'status': 'success',
                    'message': 'HDX data sync completed',
                    'records_processed': sync_log.records_processed,
                    'records_created': records_created,
                    'sync_duration': (sync_log.sync_end - sync_log.sync_start).total_seconds()
                })

            except Exception as e:
                sync_log.sync_end = timezone.now()
                sync_log.status = 'failed'
                sync_log.error_message = str(e)
                sync_log.save()
                raise

        except Exception as e:
            logger.error(f"HDX sync failed: {e}")
            return Response({
                'status': 'error',
                'message': f'HDX sync failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def sync_dtm_data(self, request):
        """Trigger DTM displacement data synchronization"""
        try:
            from_date = request.data.get('from_date', '2023-04-15')
            to_date = request.data.get('to_date', date.today().isoformat())

            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

            # Get or create DTM data source
            dtm_source, created = ExternalDataSource.objects.get_or_create(
                platform='iom_dtm',
                name='IOM DTM Sudan Displacement Data',
                defaults={
                    'api_endpoint': 'https://dtm.iom.int/api',
                    'is_active': True
                }
            )

            # Start sync log
            sync_log = DataSyncLog.objects.create(
                source=dtm_source,
                sync_start=timezone.now(),
                status='running',
                date_from=from_date,
                date_to=to_date
            )

            try:
                dtm_service = get_dtm_service()

                # Get comprehensive displacement data
                displacement_data = dtm_service.get_comprehensive_displacement_data(
                    from_date=from_date,
                    to_date=to_date
                )

                records_created = 0

                # Process displacement records
                for data_type, records in displacement_data.items():
                    for record in records:
                        # Create SudanCrisisData record
                        crisis_data, created = SudanCrisisData.objects.get_or_create(
                            source=dtm_source,
                            external_id=str(record.get('id', f"dtm_{data_type}_{records_created}")),
                            defaults={
                                'data_type': 'displacement',
                                'title': f"DTM {data_type.title()} - {record.get('location_name', 'Sudan')}",
                                'description': f"IOM DTM {data_type} data for Sudan",
                                'crisis_date': from_date,
                                'report_date': date.today(),
                                'location_name': record.get('location_name', 'Sudan'),
                                'admin_level': str(record.get('admin_level', '')),
                                'raw_data': record,
                                'url': f"https://dtm.iom.int/sudan"
                            }
                        )

                        if created:
                            # Create specific displacement data record
                            DisplacementData.objects.create(
                                crisis_data=crisis_data,
                                idp_individuals=record.get('idp_individuals'),
                                idp_families=record.get('idp_families'),
                                returnee_individuals=record.get('returnee_individuals'),
                                returnee_families=record.get('returnee_families'),
                                departure_location=record.get('departure_location', ''),
                                arrival_location=record.get('arrival_location', ''),
                                site_type=record.get('site_type', ''),
                                site_name=record.get('site_name', '')
                            )
                            records_created += 1

                # Complete sync log
                sync_log.sync_end = timezone.now()
                sync_log.status = 'completed'
                sync_log.records_processed = sum(len(records) for records in displacement_data.values())
                sync_log.records_created = records_created
                sync_log.save()

                dtm_source.last_sync = timezone.now()
                dtm_source.save()

                return Response({
                    'status': 'success',
                    'message': 'DTM data sync completed',
                    'records_processed': sync_log.records_processed,
                    'records_created': records_created
                })

            except Exception as e:
                sync_log.sync_end = timezone.now()
                sync_log.status = 'failed'
                sync_log.error_message = str(e)
                sync_log.save()
                raise

        except Exception as e:
            logger.error(f"DTM sync failed: {e}")
            return Response({
                'status': 'error',
                'message': f'DTM sync failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def test_connections(self, request):
        """Test connections to all external humanitarian APIs"""
        results = {}

        # Test HDX connection
        try:
            hdx_service = get_hdx_service()
            results['hdx'] = {
                'status': 'success' if hdx_service.test_connection() else 'failed',
                'service': 'Humanitarian Data Exchange'
            }
        except Exception as e:
            results['hdx'] = {
                'status': 'error',
                'service': 'Humanitarian Data Exchange',
                'error': str(e)
            }

        # Test HDX HAPI connection
        try:
            hapi_service = get_hdx_hapi_service()
            results['hdx_hapi'] = {
                'status': 'success' if hapi_service.test_connection() else 'failed',
                'service': 'HDX Humanitarian API'
            }
        except Exception as e:
            results['hdx_hapi'] = {
                'status': 'error',
                'service': 'HDX Humanitarian API',
                'error': str(e)
            }

        # Test DTM connection
        try:
            dtm_service = get_dtm_service()
            results['dtm'] = {
                'status': 'success' if dtm_service.test_connection() else 'failed',
                'service': 'IOM Displacement Tracking Matrix'
            }
        except Exception as e:
            results['dtm'] = {
                'status': 'error',
                'service': 'IOM Displacement Tracking Matrix',
                'error': str(e)
            }

        # Test UNHCR connection
        try:
            unhcr_service = get_unhcr_service()
            results['unhcr'] = {
                'status': 'success' if unhcr_service.test_connection() else 'failed',
                'service': 'UNHCR Refugee Data Finder'
            }
        except Exception as e:
            results['unhcr'] = {
                'status': 'error',
                'service': 'UNHCR Refugee Data Finder',
                'error': str(e)
            }

        # Test FTS connection
        try:
            fts_service = get_fts_service()
            results['fts'] = {
                'status': 'success' if fts_service.test_connection() else 'failed',
                'service': 'OCHA Financial Tracking Service'
            }
        except Exception as e:
            results['fts'] = {
                'status': 'error',
                'service': 'OCHA Financial Tracking Service',
                'error': str(e)
            }

        return Response({
            'connections': results,
            'tested_at': timezone.now().isoformat()
        })

    def _map_hdx_data_type(self, hdx_type: str) -> str:
        """Map HDX data types to our internal data types"""
        mapping = {
            'population': 'displacement',
            'funding': 'funding',
            'needs': 'needs',
            'conflict': 'conflict',
            'food_security': 'food_security'
        }
        return mapping.get(hdx_type, 'needs')
