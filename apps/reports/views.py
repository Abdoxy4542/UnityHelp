from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import FieldReport, ReportAnalysis, ReportTag
from .serializers import (
    FieldReportListSerializer, FieldReportDetailSerializer,
    FieldReportCreateSerializer, FieldReportUpdateSerializer,
    ReportAnalysisSerializer, ReportTagSerializer
)


class FieldReportViewSet(viewsets.ModelViewSet):
    queryset = FieldReport.objects.select_related('site', 'reporter', 'verified_by').prefetch_related('analyses', 'tags__tag')
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['site', 'report_type', 'priority', 'status', 'reporter']
    search_fields = ['title', 'text_content', 'site__name']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FieldReportCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FieldReportUpdateSerializer
        elif self.action == 'list':
            return FieldReportListSerializer
        return FieldReportDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user role
        user = self.request.user
        if hasattr(user, 'role'):
            if user.role == 'GSO':
                # GSOs can only see reports from their sites
                if hasattr(user, 'managed_sites'):
                    queryset = queryset.filter(site__in=user.managed_sites.all())
            elif user.role in ['NGO_USER', 'PUBLIC_USER']:
                # Regular users can only see their own reports
                queryset = queryset.filter(reporter=user)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get report statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_reports': queryset.count(),
            'by_status': dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_priority': dict(queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_type': dict(queryset.values('report_type').annotate(count=Count('id')).values_list('report_type', 'count')),
            'pending_review': queryset.filter(status='pending').count(),
            'with_media': queryset.filter(Q(voice_file__isnull=False) | Q(image_file__isnull=False)).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent reports (last 24 hours)"""
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        recent_reports = self.get_queryset().filter(created_at__gte=last_24h)
        serializer = self.get_serializer(recent_reports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get urgent reports"""
        urgent_reports = self.get_queryset().filter(priority='urgent', status__in=['pending', 'processing'])
        serializer = self.get_serializer(urgent_reports, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a report"""
        report = self.get_object()
        
        if report.status not in ['processed']:
            return Response(
                {'error': 'Report must be processed before verification'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification_notes = request.data.get('verification_notes', '')
        
        report.status = 'verified'
        report.verified_by = request.user
        report.verified_at = timezone.now()
        report.verification_notes = verification_notes
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a report"""
        report = self.get_object()
        
        rejection_reason = request.data.get('verification_notes', '')
        if not rejection_reason:
            return Response(
                {'error': 'Rejection reason is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.status = 'rejected'
        report.verified_by = request.user
        report.verified_at = timezone.now()
        report.verification_notes = rejection_reason
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process_ai(self, request, pk=None):
        """Trigger AI processing for a report"""
        report = self.get_object()
        
        if report.status != 'pending':
            return Response(
                {'error': 'Report must be pending to start AI processing'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to processing
        report.status = 'processing'
        report.save()
        
        # TODO: Integrate with OpenAI GPT-4 processing
        # For now, return a placeholder response
        return Response({
            'message': 'AI processing started',
            'report_id': report.id,
            'status': 'processing'
        })


class ReportAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportAnalysis.objects.select_related('report')
    serializer_class = ReportAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report', 'analysis_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply same filtering as FieldReportViewSet
        user = self.request.user
        if hasattr(user, 'role'):
            if user.role == 'GSO':
                if hasattr(user, 'managed_sites'):
                    queryset = queryset.filter(report__site__in=user.managed_sites.all())
            elif user.role in ['NGO_USER', 'PUBLIC_USER']:
                queryset = queryset.filter(report__reporter=user)
        
        return queryset


class ReportTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportTag.objects.all()
    serializer_class = ReportTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_ar']
    ordering = ['name']
