"""
Reports MCP Server for UnityAid
Provides access to field reports, media attachments, and AI analysis data
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from django.db.models import Q, Count, Avg, Max
from django.contrib.auth import get_user_model

from apps.reports.models import FieldReport, ReportAnalysis, ReportTag, ReportTagging
from .base import BaseMCPServer, MCPResponse, MCPDataError
from .formatters import data_formatter, humanitarian_formatter
from .schemas import REPORTS_SERVER_METHODS

User = get_user_model()
logger = logging.getLogger(__name__)


class ReportsMCPServer(BaseMCPServer):
    """MCP Server for UnityAid Reports app data access"""

    def __init__(self):
        super().__init__("reports")

    def get_available_methods(self) -> List[str]:
        """Return list of available methods"""
        return list(REPORTS_SERVER_METHODS.keys())

    def get_method_schema(self, method: str) -> Dict:
        """Return JSON schema for method parameters"""
        return REPORTS_SERVER_METHODS.get(method, {})

    def handle_get_all_reports(self, params: Dict, user=None) -> MCPResponse:
        """
        Get all field reports with filtering and pagination

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with reports data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'reports'):
                return self.error_response("Insufficient permissions to read reports data")

            # Start with base queryset
            queryset = FieldReport.objects.select_related(
                'site', 'site__state', 'site__locality', 'reporter', 'verified_by'
            ).prefetch_related('analyses', 'tags__tag').all()

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    queryset = queryset.filter(site_id__in=accessible_sites)

            # Apply filters
            queryset = self._apply_report_filters(queryset, params)

            # Apply spatial filters if provided
            queryset = self._apply_spatial_filters(queryset, params)

            # Apply date range filters
            queryset = self._apply_date_filters(queryset, params)

            # Apply search
            if params.get('search'):
                search_term = params['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(text_content__icontains=search_term) |
                    Q(site__name__icontains=search_term) |
                    Q(site__name_ar__icontains=search_term) |
                    Q(reporter__username__icontains=search_term)
                )

            # Apply ordering
            order_by = params.get('order_by', '-created_at')
            queryset = queryset.order_by(order_by)

            # Pagination
            page = params.get('page', 1)
            per_page = params.get('per_page', 50)
            paginated_data = self.paginate_queryset(queryset, page, per_page)

            # Serialize data
            serialized_reports = []
            for report in paginated_data['results']:
                report_data = self._serialize_report(
                    report,
                    include_media=params.get('include_media', True),
                    include_analysis=params.get('include_analysis', False)
                )
                serialized_reports.append(report_data)

            return self.success_response(
                data=serialized_reports,
                metadata=paginated_data['metadata']
            )

        except Exception as e:
            logger.error(f"Error in get_all_reports: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch reports: {str(e)}")

    def handle_get_report_by_id(self, params: Dict, user=None) -> MCPResponse:
        """
        Get detailed information for a specific report

        Args:
            params: Request parameters with report_id
            user: Authenticated user (optional)

        Returns:
            MCPResponse with report data
        """
        try:
            report_id = params.get('report_id')
            if not report_id:
                return self.error_response("report_id parameter is required")

            # Check permissions
            if user and not self.check_permissions(user, 'read', 'reports'):
                return self.error_response("Insufficient permissions to read report data")

            # Get report
            try:
                report = FieldReport.objects.select_related(
                    'site', 'site__state', 'site__locality', 'reporter', 'verified_by'
                ).prefetch_related('analyses', 'tags__tag').get(id=report_id)
            except FieldReport.DoesNotExist:
                return self.error_response(f"Report with ID {report_id} not found")

            # Check user access to specific report
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None and report.site_id not in accessible_sites:
                    return self.error_response("Access denied to this report")

            # Serialize report with full details
            report_data = self._serialize_report(
                report,
                include_media=params.get('include_media', True),
                include_analysis=params.get('include_analysis', True),
                include_tags=True,
                full_details=True
            )

            return self.success_response(data=report_data)

        except Exception as e:
            logger.error(f"Error in get_report_by_id: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch report: {str(e)}")

    def handle_search_reports(self, params: Dict, user=None) -> MCPResponse:
        """
        Full-text search in reports (Arabic and English)

        Args:
            params: Request parameters with search query
            user: Authenticated user (optional)

        Returns:
            MCPResponse with matching reports
        """
        try:
            query = params.get('query')
            if not query:
                return self.error_response("query parameter is required")

            # Check permissions
            if user and not self.check_permissions(user, 'read', 'reports'):
                return self.error_response("Insufficient permissions to search reports")

            # Base queryset
            queryset = FieldReport.objects.select_related(
                'site', 'reporter'
            ).prefetch_related('tags__tag')

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    queryset = queryset.filter(site_id__in=accessible_sites)

            # Full-text search across multiple fields
            search_filter = (
                Q(title__icontains=query) |
                Q(text_content__icontains=query) |
                Q(site__name__icontains=query) |
                Q(site__name_ar__icontains=query) |
                Q(tags__tag__name__icontains=query) |
                Q(tags__tag__name_ar__icontains=query)
            )

            queryset = queryset.filter(search_filter).distinct()

            # Order by relevance (simplified scoring)
            # In production, consider using full-text search features
            queryset = queryset.order_by('-created_at')

            # Pagination
            page = params.get('page', 1)
            per_page = params.get('per_page', 20)
            paginated_data = self.paginate_queryset(queryset, page, per_page)

            # Serialize results
            search_results = []
            for report in paginated_data['results']:
                report_data = self._serialize_report(
                    report,
                    include_media=False,
                    include_analysis=False,
                    include_search_highlights=True,
                    search_query=query
                )
                search_results.append(report_data)

            return self.success_response(
                data=search_results,
                metadata={
                    **paginated_data['metadata'],
                    'search_query': query,
                    'search_time': datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error in search_reports: {e}", exc_info=True)
            return self.error_response(f"Failed to search reports: {str(e)}")

    def handle_get_reports_summary(self, params: Dict, user=None) -> MCPResponse:
        """
        Get summary statistics for reports

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with summary data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'reports'):
                return self.error_response("Insufficient permissions to read reports data")

            # Base queryset
            queryset = FieldReport.objects.all()

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    queryset = queryset.filter(site_id__in=accessible_sites)

            # Apply filters
            queryset = self._apply_report_filters(queryset, params)
            queryset = self._apply_date_filters(queryset, params)

            # Calculate summary statistics
            summary_stats = queryset.aggregate(
                total_reports=Count('id'),
                urgent_reports=Count('id', filter=Q(priority='urgent')),
                high_priority_reports=Count('id', filter=Q(priority='high')),
                processed_reports=Count('id', filter=Q(status__in=['processed', 'verified'])),
                verified_reports=Count('id', filter=Q(status='verified')),
                reports_with_media=Count('id', filter=Q(voice_file__isnull=False) | Q(image_file__isnull=False)),
                avg_ai_confidence=Avg('analyses__ai_confidence')
            )

            # Count by status, priority, and type
            status_breakdown = dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            priority_breakdown = dict(queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))
            type_breakdown = dict(queryset.values('report_type').annotate(count=Count('id')).values_list('report_type', 'count'))

            # Recent activity
            recent_reports = queryset.filter(
                created_at__gte=datetime.now().replace(hour=0, minute=0, second=0)
            ).count()

            # Top reporting sites
            top_sites = dict(
                queryset.values('site__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
                .values_list('site__name', 'count')
            )

            # Most active reporters
            top_reporters = dict(
                queryset.values('reporter__username')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
                .values_list('reporter__username', 'count')
            )

            summary_data = {
                'overview': summary_stats,
                'breakdowns': {
                    'by_status': status_breakdown,
                    'by_priority': priority_breakdown,
                    'by_type': type_breakdown
                },
                'activity': {
                    'reports_today': recent_reports,
                    'processing_rate': (
                        summary_stats['processed_reports'] / summary_stats['total_reports'] * 100
                        if summary_stats['total_reports'] else 0
                    ),
                    'verification_rate': (
                        summary_stats['verified_reports'] / summary_stats['total_reports'] * 100
                        if summary_stats['total_reports'] else 0
                    )
                },
                'top_contributors': {
                    'sites': top_sites,
                    'reporters': top_reporters
                }
            }

            return self.success_response(data=summary_data)

        except Exception as e:
            logger.error(f"Error in get_reports_summary: {e}", exc_info=True)
            return self.error_response(f"Failed to generate summary: {str(e)}")

    def handle_get_urgent_reports(self, params: Dict, user=None) -> MCPResponse:
        """
        Get urgent and high-priority reports requiring immediate attention

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with urgent reports data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'reports'):
                return self.error_response("Insufficient permissions to read reports")

            # Get urgent and high-priority reports
            queryset = FieldReport.objects.select_related(
                'site', 'reporter'
            ).filter(priority__in=['urgent', 'high']).order_by('-created_at')

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    queryset = queryset.filter(site_id__in=accessible_sites)

            # Apply date filter if provided
            if params.get('hours'):
                try:
                    hours = int(params['hours'])
                    cutoff_time = datetime.now() - timedelta(hours=hours)
                    queryset = queryset.filter(created_at__gte=cutoff_time)
                except ValueError:
                    pass

            # Limit results
            limit = params.get('limit', 50)
            queryset = queryset[:limit]

            # Serialize reports
            urgent_reports = []
            for report in queryset:
                report_data = self._serialize_report(
                    report,
                    include_media=True,
                    include_analysis=True,
                    include_urgency_context=True
                )
                urgent_reports.append(report_data)

            return self.success_response(
                data=urgent_reports,
                metadata={
                    'total_urgent': len(urgent_reports),
                    'filter_applied': f"Last {params.get('hours', 24)} hours" if params.get('hours') else "All time"
                }
            )

        except Exception as e:
            logger.error(f"Error in get_urgent_reports: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch urgent reports: {str(e)}")

    def _apply_report_filters(self, queryset, params: Dict):
        """Apply report-specific filters to queryset"""

        # Filter by site
        if params.get('site_id'):
            queryset = queryset.filter(site_id=params['site_id'])

        # Filter by reporter
        if params.get('reporter_id') or params.get('gso_id'):
            reporter_id = params.get('reporter_id') or params.get('gso_id')
            queryset = queryset.filter(reporter_id=reporter_id)

        # Filter by priority level
        if params.get('priority') or params.get('urgency_level'):
            priority = params.get('priority') or params.get('urgency_level')
            queryset = queryset.filter(priority=priority)

        # Filter by status
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])

        # Filter by report type
        if params.get('report_type'):
            queryset = queryset.filter(report_type=params['report_type'])

        # Filter by media presence
        if params.get('has_media') is not None:
            if params['has_media']:
                queryset = queryset.filter(
                    Q(voice_file__isnull=False) | Q(image_file__isnull=False)
                )
            else:
                queryset = queryset.filter(
                    voice_file__isnull=True, image_file__isnull=True
                )

        # Filter by verification status
        if params.get('verified') is not None:
            if params['verified']:
                queryset = queryset.filter(status='verified')
            else:
                queryset = queryset.exclude(status='verified')

        return queryset

    def _apply_spatial_filters(self, queryset, params: Dict):
        """Apply spatial filters to queryset based on site locations"""

        # Filter by site bounds (delegated to site locations)
        if params.get('bounds'):
            try:
                minx, miny, maxx, maxy = params['bounds']
                # Filter by site coordinates within bounds
                site_ids = []
                for report in queryset:
                    if report.site.coordinates:
                        lng, lat = report.site.coordinates
                        if minx <= lng <= maxx and miny <= lat <= maxy:
                            site_ids.append(report.site.id)
                queryset = queryset.filter(site_id__in=site_ids)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid bounds parameter: {e}")

        return queryset

    def _apply_date_filters(self, queryset, params: Dict):
        """Apply date range filters to queryset"""

        if params.get('from_date'):
            try:
                from_date = datetime.strptime(params['from_date'], '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=from_date)
            except ValueError:
                logger.warning("Invalid from_date format")

        if params.get('to_date'):
            try:
                to_date = datetime.strptime(params['to_date'], '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=to_date)
            except ValueError:
                logger.warning("Invalid to_date format")

        return queryset

    def _serialize_report(self, report: FieldReport, include_media: bool = True,
                         include_analysis: bool = False, include_tags: bool = False,
                         full_details: bool = False, include_search_highlights: bool = False,
                         search_query: str = None, include_urgency_context: bool = False) -> Dict:
        """
        Serialize FieldReport model to dictionary

        Args:
            report: FieldReport model instance
            include_media: Include media file information
            include_analysis: Include AI analysis data
            include_tags: Include report tags
            full_details: Include all available details
            include_search_highlights: Include search result highlights
            search_query: Search query for highlighting
            include_urgency_context: Include urgency context information

        Returns:
            Serialized report data
        """
        data = {
            'id': report.id,
            'title': report.title,
            'text_content': report.text_content,
            'report_type': report.report_type,
            'report_type_display': report.get_report_type_display(),
            'priority': report.priority,
            'priority_display': report.get_priority_display(),
            'status': report.status,
            'status_display': report.get_status_display(),
            'location_coordinates': report.location_coordinates,
            'has_media': report.has_media,
            'is_processed': report.is_processed,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat(),
            'processed_at': report.processed_at.isoformat() if report.processed_at else None,
            'verified_at': report.verified_at.isoformat() if report.verified_at else None
        }

        # Site information
        if report.site:
            data['site'] = {
                'id': report.site.id,
                'name': report.site.name,
                'name_ar': report.site.name_ar,
                'site_type': report.site.site_type,
                'coordinates': report.site.coordinates,
                'state': report.site.state.name if report.site.state else None,
                'locality': report.site.locality.name if report.site.locality else None
            }

        # Reporter information
        if report.reporter:
            data['reporter'] = {
                'id': report.reporter.id,
                'username': report.reporter.username,
                'full_name': f"{report.reporter.first_name} {report.reporter.last_name}".strip(),
            }

        # Verifier information
        if report.verified_by:
            data['verified_by'] = {
                'id': report.verified_by.id,
                'username': report.verified_by.username,
                'full_name': f"{report.verified_by.first_name} {report.verified_by.last_name}".strip(),
            }
            if full_details:
                data['verification_notes'] = report.verification_notes

        # Media files
        if include_media:
            data['media'] = {
                'voice_file': {
                    'url': report.voice_file.url if report.voice_file else None,
                    'size': report.voice_file.size if report.voice_file else None
                },
                'image_file': {
                    'url': report.image_file.url if report.image_file else None,
                    'size': report.image_file.size if report.image_file else None
                }
            }

        # AI analysis data
        if include_analysis and hasattr(report, 'analyses'):
            analyses = []
            for analysis in report.analyses.all():
                analysis_data = {
                    'id': analysis.id,
                    'analysis_type': analysis.analysis_type,
                    'analysis_type_display': analysis.get_analysis_type_display(),
                    'ai_confidence': analysis.ai_confidence,
                    'analysis_data': analysis.analysis_data,
                    'extracted_entities': analysis.extracted_entities,
                    'key_insights': analysis.key_insights,
                    'model_version': analysis.model_version,
                    'processing_time': analysis.processing_time,
                    'created_at': analysis.created_at.isoformat()
                }
                analyses.append(analysis_data)
            data['analyses'] = analyses

        # Tags
        if include_tags and hasattr(report, 'tags'):
            tags = []
            for tagging in report.tags.all():
                tag_data = {
                    'name': tagging.tag.name,
                    'name_ar': tagging.tag.name_ar,
                    'color': tagging.tag.color,
                    'confidence': tagging.confidence,
                    'auto_generated': tagging.auto_generated
                }
                tags.append(tag_data)
            data['tags'] = tags

        # Search highlights
        if include_search_highlights and search_query:
            # Simple highlighting - in production, use proper search highlighting
            highlighted_fields = {}
            if search_query.lower() in report.title.lower():
                highlighted_fields['title'] = report.title
            if search_query.lower() in report.text_content.lower():
                highlighted_fields['text_content'] = report.text_content[:200] + "..."
            data['search_highlights'] = highlighted_fields

        # Urgency context
        if include_urgency_context:
            time_since_created = datetime.now() - report.created_at.replace(tzinfo=None)
            data['urgency_context'] = {
                'is_urgent': report.priority == 'urgent',
                'is_high_priority': report.priority in ['urgent', 'high'],
                'hours_since_created': round(time_since_created.total_seconds() / 3600, 1),
                'requires_immediate_attention': (
                    report.priority == 'urgent' and
                    report.status == 'pending' and
                    time_since_created.total_seconds() > 3600  # More than 1 hour
                )
            }

        return data


# Create server instance
reports_server = ReportsMCPServer()