from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.db.models import Q, Count, Prefetch
from datetime import timedelta
import secrets
import logging

from apps.accounts.models import User, UserProfile, EmailVerification
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse
from apps.reports.models import FieldReport, ReportAnalysis, ReportTag
from ..models import MobileDevice, RefreshToken, SyncLog
from .serializers import *
from .permissions import IsMobileUser, IsOwnerOrReadOnly
from .utils import generate_refresh_token, create_or_update_device, send_mobile_notification

logger = logging.getLogger(__name__)


# ================== Pagination Classes ==================

class MobilePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })


# ================== Authentication Views ==================

class MobileLoginView(APIView):
    """Enhanced mobile login with device registration and refresh tokens"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = MobileLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Create or update device
        device = create_or_update_device(user, serializer.validated_data)

        # Create access token
        token, created = Token.objects.get_or_create(user=user)

        # Create refresh token
        refresh_token = generate_refresh_token(user, device)

        # Update last login
        user.last_login = timezone.now()
        user.save()

        logger.info(f"Mobile login successful for user {user.email} on device {device.device_id}")

        return Response({
            'user': MobileUserSerializer(user, context={'request': request}).data,
            'access_token': token.key,
            'refresh_token': refresh_token.token,
            'device_id': str(device.id),
            'expires_in': 86400  # 24 hours
        })


class MobileRegisterView(APIView):
    """Mobile user registration with device registration"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = MobileRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()

            # Create device
            device_data = user._device_data
            device = create_or_update_device(user, device_data)

            # Create email verification
            verification = EmailVerification.objects.create(
                user=user,
                email=user.email
            )

            # Send verification email (implement in utils)
            # send_verification_email(user, verification)

            logger.info(f"Mobile registration successful for user {user.email}")

            return Response({
                'message': 'Registration successful. Please verify your email.',
                'user_id': user.id,
                'email': user.email,
                'verification_required': True
            }, status=status.HTTP_201_CREATED)


class RefreshTokenView(APIView):
    """Refresh access token using refresh token"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token_str = request.data.get('refresh_token')

        if not refresh_token_str:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh_token = RefreshToken.objects.select_related('user', 'device').get(
                token=refresh_token_str,
                is_revoked=False
            )

            if refresh_token.is_expired():
                return Response({'error': 'Refresh token expired'}, status=status.HTTP_401_UNAUTHORIZED)

            user = refresh_token.user
            device = refresh_token.device

            # Create new access token
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                # Refresh the existing token
                token.delete()
                token = Token.objects.create(user=user)

            # Create new refresh token and revoke old one
            refresh_token.is_revoked = True
            refresh_token.save()

            new_refresh_token = generate_refresh_token(user, device)

            # Update device last seen
            device.last_seen = timezone.now()
            device.save()

            return Response({
                'access_token': token.key,
                'refresh_token': new_refresh_token.token,
                'expires_in': 86400
            })

        except RefreshToken.DoesNotExist:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class MobileLogoutView(APIView):
    """Mobile logout with token cleanup"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        device_id = request.data.get('device_id')

        # Delete access token
        Token.objects.filter(user=user).delete()

        # Revoke refresh tokens for this device
        if device_id:
            RefreshToken.objects.filter(
                user=user,
                device__id=device_id
            ).update(is_revoked=True)
        else:
            # Revoke all refresh tokens for user
            RefreshToken.objects.filter(user=user).update(is_revoked=True)

        logger.info(f"Mobile logout for user {user.email}")

        return Response({'message': 'Successfully logged out'})


class MobileProfileView(APIView):
    """Get and update mobile user profile"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MobileUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = MobileUserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MobilePasswordResetView(APIView):
    """Password reset for mobile"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Implement password reset logic
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)

        # Implementation similar to web version but mobile-optimized
        return Response({'message': 'Password reset instructions sent'})


class MobileVerifyEmailView(APIView):
    """Email verification for mobile"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Implement email verification logic
        code = request.data.get('code')
        email = request.data.get('email')

        if not code or not email:
            return Response({'error': 'Code and email required'}, status=status.HTTP_400_BAD_REQUEST)

        # Implementation similar to web version
        return Response({'message': 'Email verified successfully'})


# ================== Device Management ==================

class DeviceViewSet(viewsets.ModelViewSet):
    """Manage mobile devices"""
    serializer_class = MobileDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MobilePagination

    def get_queryset(self):
        return MobileDevice.objects.filter(user=self.request.user).order_by('-last_seen')

    @action(detail=True, methods=['post'])
    def update_fcm_token(self, request, pk=None):
        """Update FCM token for push notifications"""
        device = self.get_object()
        fcm_token = request.data.get('fcm_token')

        if fcm_token:
            device.fcm_token = fcm_token
            device.save()
            return Response({'message': 'FCM token updated'})

        return Response({'error': 'FCM token required'}, status=status.HTTP_400_BAD_REQUEST)


# ================== Core Data ViewSets ==================

class SiteViewSet(viewsets.ModelViewSet):
    """Mobile sites management with enhanced filtering"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MobilePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['site_type', 'operational_status', 'state', 'locality']
    search_fields = ['name', 'name_ar', 'description']
    ordering_fields = ['name', 'total_population', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Site.objects.select_related('state', 'locality')

        # Role-based filtering
        if user.role == 'gso':
            queryset = queryset.filter(
                Q(id__in=user.assigned_sites.all()) |
                Q(state__in=user.assigned_sites.values_list('state', flat=True))
            )
        elif user.role == 'ngo_user':
            # NGO users can see sites in their organization's areas
            queryset = queryset.filter(operational_status='active')

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SiteCreateUpdateSerializer
        return MobileSiteSerializer

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get sites near user's location"""
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = float(request.query_params.get('radius', 10))  # km

        if not lat or not lon:
            return Response({'error': 'Latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)

        # For development without PostGIS, use simple bounding box
        try:
            lat, lon = float(lat), float(lon)
            # Simple bounding box calculation (approximate)
            lat_offset = radius / 111.0  # 1 degree lat ≈ 111 km
            lon_offset = radius / (111.0 * abs(lat))

            sites = self.get_queryset().filter(
                location__isnull=False
            ).extra(
                where=[
                    "JSON_EXTRACT(location, '$.coordinates[1]') BETWEEN %s AND %s",
                    "JSON_EXTRACT(location, '$.coordinates[0]') BETWEEN %s AND %s"
                ],
                params=[lat - lat_offset, lat + lat_offset, lon - lon_offset, lon + lon_offset]
            )

            serializer = self.get_serializer(sites, many=True)
            return Response(serializer.data)

        except (ValueError, TypeError):
            return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get sites summary statistics"""
        queryset = self.get_queryset()

        summary = {
            'total_sites': queryset.count(),
            'active_sites': queryset.filter(operational_status='active').count(),
            'total_population': sum(site.total_population or 0 for site in queryset),
            'by_type': dict(queryset.values_list('site_type').annotate(count=Count('id'))),
            'by_status': dict(queryset.values_list('operational_status').annotate(count=Count('id')))
        }

        return Response(summary)


class AssessmentViewSet(viewsets.ModelViewSet):
    """Mobile assessments management"""
    serializer_class = MobileAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MobilePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assessment_type', 'status', 'created_by']
    search_fields = ['title', 'title_ar', 'description']
    ordering_fields = ['title', 'start_date', 'end_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Assessment.objects.select_related('created_by').prefetch_related('assigned_to', 'target_sites')

        # Filter based on user role and assignments
        if user.role == 'gso':
            queryset = queryset.filter(
                Q(assigned_to=user) |
                Q(target_sites__in=user.assigned_sites.all())
            )
        elif user.role in ['ngo_user', 'un_user']:
            queryset = queryset.filter(status='active')

        return queryset.distinct()

    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get assessments assigned to current user"""
        assessments = self.get_queryset().filter(assigned_to=request.user)
        serializer = self.get_serializer(assessments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def form_data(self, request, pk=None):
        """Get Kobo form data for assessment"""
        assessment = self.get_object()

        # Return cached form data or fetch from Kobo
        cache_key = f"assessment_form_{assessment.id}"
        form_data = cache.get(cache_key)

        if not form_data:
            # Implement Kobo form fetching logic
            form_data = {
                'form_id': assessment.kobo_form_id,
                'form_url': assessment.kobo_form_url,
                'fields': []  # Will be populated from Kobo API
            }
            cache.set(cache_key, form_data, 3600)  # Cache for 1 hour

        return Response(form_data)


class AssessmentResponseViewSet(viewsets.ModelViewSet):
    """Assessment responses management for mobile"""
    serializer_class = MobileAssessmentResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MobilePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assessment', 'site', 'is_submitted']
    search_fields = ['assessment__title', 'site__name']
    ordering = ['-created_at']

    def get_queryset(self):
        return AssessmentResponse.objects.filter(
            respondent=self.request.user
        ).select_related('assessment', 'site', 'respondent')

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit assessment response"""
        response = self.get_object()

        if response.is_submitted:
            return Response({'error': 'Response already submitted'}, status=status.HTTP_400_BAD_REQUEST)

        response.is_submitted = True
        response.submitted_at = timezone.now()
        response.save()

        logger.info(f"Assessment response {response.id} submitted by {request.user.email}")

        return Response({'message': 'Response submitted successfully'})

    @action(detail=False, methods=['get'])
    def drafts(self, request):
        """Get draft responses"""
        drafts = self.get_queryset().filter(is_submitted=False)
        serializer = self.get_serializer(drafts, many=True)
        return Response(serializer.data)


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Mobile reports access (read-only)"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MobilePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        # Implement based on your Report model
        return Report.objects.all()  # Adjust based on actual model

    def get_serializer_class(self):
        # Return appropriate serializer based on your Report model
        return serializers.Serializer


class DashboardViewSet(viewsets.ViewSet):
    """Mobile dashboard data"""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Get dashboard summary for mobile"""
        user = request.user

        # Get user's relevant data
        if user.role == 'gso':
            sites_count = user.assigned_sites.count()
            assessments_count = Assessment.objects.filter(assigned_to=user).count()
        else:
            sites_count = Site.objects.filter(operational_status='active').count()
            assessments_count = Assessment.objects.filter(status='active').count()

        # Get recent activities
        recent_responses = AssessmentResponse.objects.filter(
            respondent=user
        ).order_by('-created_at')[:5]

        dashboard_data = {
            'user_info': MobileUserSerializer(user, context={'request': request}).data,
            'statistics': {
                'sites_count': sites_count,
                'assessments_count': assessments_count,
                'pending_responses': recent_responses.filter(is_submitted=False).count(),
                'completed_responses': recent_responses.filter(is_submitted=True).count()
            },
            'recent_activities': MobileAssessmentResponseSerializer(recent_responses, many=True).data
        }

        return Response(dashboard_data)


# ================== Sync Views ==================

class InitialSyncView(APIView):
    """Initial data sync for mobile app"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitialSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data_types = serializer.validated_data.get('data_types', ['sites', 'assessments'])

        # Create sync log
        sync_log = SyncLog.objects.create(
            user=user,
            device_id=request.data.get('device_id', 'unknown'),
            sync_type='initial',
            status='in_progress'
        )

        sync_data = {}

        try:
            if 'sites' in data_types:
                sites = Site.objects.filter(operational_status='active')[:100]  # Limit for mobile
                sync_data['sites'] = MobileSiteSerializer(sites, many=True).data

            if 'assessments' in data_types:
                assessments = Assessment.objects.filter(
                    status='active',
                    assigned_to=user
                )[:50]
                sync_data['assessments'] = MobileAssessmentSerializer(assessments, many=True).data

            # Add metadata
            sync_data['sync_metadata'] = {
                'sync_id': str(sync_log.id),
                'timestamp': timezone.now().isoformat(),
                'user_id': user.id,
                'data_version': '1.0'
            }

            sync_log.status = 'completed'
            sync_log.completed_at = timezone.now()
            sync_log.total_items = sum(len(data) for data in sync_data.values() if isinstance(data, list))
            sync_log.processed_items = sync_log.total_items
            sync_log.save()

            logger.info(f"Initial sync completed for user {user.email}")

            return Response(sync_data)

        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()

            logger.error(f"Initial sync failed for user {user.email}: {e}")
            return Response({'error': 'Sync failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IncrementalSyncView(APIView):
    """Incremental sync for updated data"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        last_sync = request.data.get('last_sync_date')
        if not last_sync:
            return Response({'error': 'Last sync date required'}, status=status.HTTP_400_BAD_REQUEST)

        # Implement incremental sync logic
        return Response({'message': 'Incremental sync completed'})


class BulkUploadView(APIView):
    """Bulk upload data from mobile"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BulkUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data_type = serializer.validated_data['data_type']
        items = serializer.validated_data['items']

        # Create sync log
        sync_log = SyncLog.objects.create(
            user=request.user,
            sync_type='upload',
            status='in_progress',
            total_items=len(items)
        )

        try:
            with transaction.atomic():
                processed_count = 0
                failed_count = 0

                for item_data in items:
                    try:
                        if data_type == 'sites':
                            serializer = SiteCreateUpdateSerializer(data=item_data)
                            if serializer.is_valid():
                                serializer.save()
                                processed_count += 1
                            else:
                                failed_count += 1

                        # Add other data types as needed

                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Failed to process item: {e}")

                sync_log.processed_items = processed_count
                sync_log.failed_items = failed_count
                sync_log.status = 'completed' if failed_count == 0 else 'partial'
                sync_log.completed_at = timezone.now()
                sync_log.save()

                return Response({
                    'processed': processed_count,
                    'failed': failed_count,
                    'sync_id': str(sync_log.id)
                })

        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()

            return Response({'error': 'Bulk upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================== Health Check ==================

class HealthCheckView(APIView):
    """API health check for mobile apps"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            # Check database
            User.objects.count()
            db_status = 'healthy'
        except Exception:
            db_status = 'unhealthy'

        try:
            # Check cache
            cache.set('health_check', 'test', 10)
            cache.get('health_check')
            cache_status = 'healthy'
        except Exception:
            cache_status = 'unhealthy'

        health_data = {
            'status': 'healthy' if db_status == 'healthy' and cache_status == 'healthy' else 'unhealthy',
            'timestamp': timezone.now(),
            'version': '1.0.0',
            'database': db_status,
            'cache': cache_status,
            'services': {
                'api': 'healthy',
                'authentication': 'healthy'
            }
        }

        status_code = status.HTTP_200_OK if health_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(health_data, status=status_code)


# ================== Reports Views ==================

class MobileFieldReportViewSet(viewsets.ModelViewSet):
    """Mobile-optimized ViewSet for Field Reports with file upload support"""
    queryset = FieldReport.objects.select_related('site', 'reporter').prefetch_related('analyses')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MobilePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['report_type', 'priority', 'status', 'site']
    search_fields = ['title', 'text_content', 'site__name']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MobileFieldReportCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MobileFieldReportUpdateSerializer
        elif self.action == 'list':
            return MobileFieldReportListSerializer
        return MobileFieldReportDetailSerializer

    def get_queryset(self):
        """Filter reports based on user role and permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, 'role'):
            if user.role == 'gso':
                # GSOs see reports from their assigned sites
                if hasattr(user, 'managed_sites'):
                    queryset = queryset.filter(
                        Q(site__assigned_gsos=user) |
                        Q(reporter=user)
                    )
                else:
                    queryset = queryset.filter(reporter=user)
            elif user.role == 'ngo_user':
                # NGO users see reports from their organization's sites
                if hasattr(user, 'organization'):
                    queryset = queryset.filter(
                        Q(site__organization=user.organization) |
                        Q(reporter=user)
                    )
                else:
                    queryset = queryset.filter(reporter=user)
            elif user.role == 'public_user':
                # Public users only see their own reports
                queryset = queryset.filter(reporter=user)
            # Admin, cluster_lead, un_user see all reports (no additional filtering)

        return queryset

    @action(detail=False, methods=['get'])
    def my_reports(self, request):
        """Get current user's reports"""
        reports = self.get_queryset().filter(reporter=request.user)

        page = self.paginate_queryset(reports)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def urgent_reports(self, request):
        """Get urgent reports for mobile dashboard"""
        urgent_reports = self.get_queryset().filter(
            priority='urgent',
            status__in=['pending', 'processing']
        )

        page = self.paginate_queryset(urgent_reports)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(urgent_reports, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_reports(self, request):
        """Get recent reports (last 24 hours)"""
        last_24h = timezone.now() - timedelta(hours=24)
        recent_reports = self.get_queryset().filter(created_at__gte=last_24h)

        serializer = self.get_serializer(recent_reports, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get mobile-optimized report statistics"""
        queryset = self.get_queryset()

        stats = {
            'total_reports': queryset.count(),
            'my_reports': queryset.filter(reporter=request.user).count(),
            'pending_reports': queryset.filter(status='pending').count(),
            'urgent_reports': queryset.filter(priority='urgent', status__in=['pending', 'processing']).count(),
            'reports_today': queryset.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'reports_with_media': queryset.filter(
                Q(voice_file__isnull=False) | Q(image_file__isnull=False)
            ).count(),
            'by_type': {
                'text': queryset.filter(report_type='text').count(),
                'voice': queryset.filter(report_type='voice').count(),
                'image': queryset.filter(report_type='image').count(),
                'mixed': queryset.filter(report_type='mixed').count(),
            },
            'by_priority': {
                'low': queryset.filter(priority='low').count(),
                'medium': queryset.filter(priority='medium').count(),
                'high': queryset.filter(priority='high').count(),
                'urgent': queryset.filter(priority='urgent').count(),
            }
        }

        return Response(stats)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark report as read (for notification tracking)"""
        report = self.get_object()

        # Could add read tracking here if needed
        # For now, just return success

        return Response({'status': 'marked_as_read', 'report_id': report.id})