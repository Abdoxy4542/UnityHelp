"""
Assessments MCP Server for UnityAid
Provides access to KoboToolbox assessments, survey responses, and analysis data
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from django.db.models import Q, Count, Avg, Max, Min
from django.contrib.auth import get_user_model

from apps.assessments.models import Assessment, AssessmentResponse, KoboIntegrationSettings
from apps.integrations.kobo_service import get_kobo_service_for_user
from .base import BaseMCPServer, MCPResponse, MCPDataError
from .formatters import data_formatter, humanitarian_formatter
from .schemas import ASSESSMENTS_SERVER_METHODS

User = get_user_model()
logger = logging.getLogger(__name__)


class AssessmentsMCPServer(BaseMCPServer):
    """MCP Server for UnityAid Assessments app data access"""

    def __init__(self):
        super().__init__("assessments")

    def get_available_methods(self) -> List[str]:
        """Return list of available methods"""
        return list(ASSESSMENTS_SERVER_METHODS.keys())

    def get_method_schema(self, method: str) -> Dict:
        """Return JSON schema for method parameters"""
        return ASSESSMENTS_SERVER_METHODS.get(method, {})

    def handle_get_all_assessments(self, params: Dict, user=None) -> MCPResponse:
        """
        Get all assessments with filtering and pagination

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with assessments data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'assessments'):
                return self.error_response("Insufficient permissions to read assessments data")

            # Start with base queryset
            queryset = Assessment.objects.select_related('created_by').prefetch_related(
                'target_sites', 'assigned_to', 'responses'
            ).all()

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    # Filter assessments that target accessible sites
                    queryset = queryset.filter(target_sites__in=accessible_sites).distinct()

            # Apply filters
            queryset = self._apply_assessment_filters(queryset, params)

            # Apply date range filters
            queryset = self._apply_date_filters(queryset, params)

            # Apply search
            if params.get('search'):
                search_term = params['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(title_ar__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(kobo_form_id__icontains=search_term)
                )

            # Apply ordering
            order_by = params.get('order_by', '-created_at')
            queryset = queryset.order_by(order_by)

            # Pagination
            page = params.get('page', 1)
            per_page = params.get('per_page', 50)
            paginated_data = self.paginate_queryset(queryset, page, per_page)

            # Serialize data
            serialized_assessments = []
            for assessment in paginated_data['results']:
                assessment_data = self._serialize_assessment(
                    assessment,
                    include_responses_summary=True,
                    include_sites=params.get('include_sites', False)
                )
                serialized_assessments.append(assessment_data)

            return self.success_response(
                data=serialized_assessments,
                metadata=paginated_data['metadata']
            )

        except Exception as e:
            logger.error(f"Error in get_all_assessments: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch assessments: {str(e)}")

    def handle_get_assessment_by_id(self, params: Dict, user=None) -> MCPResponse:
        """
        Get detailed information for a specific assessment

        Args:
            params: Request parameters with assessment_id
            user: Authenticated user (optional)

        Returns:
            MCPResponse with assessment data
        """
        try:
            assessment_id = params.get('assessment_id')
            if not assessment_id:
                return self.error_response("assessment_id parameter is required")

            # Check permissions
            if user and not self.check_permissions(user, 'read', 'assessments'):
                return self.error_response("Insufficient permissions to read assessment data")

            # Get assessment
            try:
                assessment = Assessment.objects.select_related('created_by').prefetch_related(
                    'target_sites', 'assigned_to', 'responses__site', 'responses__respondent'
                ).get(id=assessment_id)
            except Assessment.DoesNotExist:
                return self.error_response(f"Assessment with ID {assessment_id} not found")

            # Check user access to assessment
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    assessment_sites = list(assessment.target_sites.values_list('id', flat=True))
                    if not any(site_id in accessible_sites for site_id in assessment_sites):
                        return self.error_response("Access denied to this assessment")

            # Serialize assessment with full details
            assessment_data = self._serialize_assessment(
                assessment,
                include_responses_summary=True,
                include_sites=True,
                include_responses_data=params.get('include_responses', False),
                full_details=True
            )

            return self.success_response(data=assessment_data)

        except Exception as e:
            logger.error(f"Error in get_assessment_by_id: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch assessment: {str(e)}")

    def handle_analyze_assessment(self, params: Dict, user=None) -> MCPResponse:
        """
        Analyze assessment data and generate insights

        Args:
            params: Request parameters with assessment_id and analysis options
            user: Authenticated user (optional)

        Returns:
            MCPResponse with analysis data
        """
        try:
            assessment_id = params.get('assessment_id')
            if not assessment_id:
                return self.error_response("assessment_id parameter is required")

            analysis_type = params.get('analysis_type', 'summary')
            compare_with = params.get('compare_with', [])

            # Check permissions
            if user and not self.check_permissions(user, 'read', 'assessments'):
                return self.error_response("Insufficient permissions to analyze assessment")

            # Get assessment
            try:
                assessment = Assessment.objects.prefetch_related(
                    'responses__site', 'target_sites'
                ).get(id=assessment_id)
            except Assessment.DoesNotExist:
                return self.error_response(f"Assessment with ID {assessment_id} not found")

            # Generate analysis based on type
            analysis_data = {}

            if analysis_type in ['summary', 'all']:
                analysis_data['summary'] = self._generate_assessment_summary(assessment)

            if analysis_type in ['trend', 'all']:
                analysis_data['trends'] = self._generate_trend_analysis(assessment)

            if analysis_type in ['comparison', 'all'] and compare_with:
                analysis_data['comparison'] = self._generate_comparison_analysis(
                    assessment, compare_with
                )

            if analysis_type in ['indicators', 'all']:
                analysis_data['indicators'] = self._extract_key_indicators(assessment)

            # Add metadata
            analysis_data['metadata'] = {
                'assessment_id': assessment.id,
                'assessment_title': assessment.title,
                'analysis_type': analysis_type,
                'generated_at': datetime.utcnow().isoformat(),
                'total_responses': assessment.response_count
            }

            return self.success_response(data=analysis_data)

        except Exception as e:
            logger.error(f"Error in analyze_assessment: {e}", exc_info=True)
            return self.error_response(f"Failed to analyze assessment: {str(e)}")

    def handle_get_kobo_forms(self, params: Dict, user=None) -> MCPResponse:
        """
        Get available Kobo forms for the user

        Args:
            params: Request parameters
            user: Authenticated user (required for Kobo access)

        Returns:
            MCPResponse with Kobo forms data
        """
        try:
            if not user:
                return self.error_response("Authentication required for Kobo form access")

            # Check permissions
            if not self.check_permissions(user, 'read', 'assessments'):
                return self.error_response("Insufficient permissions to access Kobo forms")

            # Get user's Kobo integration settings
            try:
                kobo_service = get_kobo_service_for_user(user)
            except Exception as e:
                return self.error_response(f"Kobo integration not configured: {str(e)}")

            # Fetch forms from Kobo
            try:
                kobo_forms = kobo_service.get_assets()

                # Filter and format forms
                formatted_forms = []
                for form in kobo_forms:
                    form_data = {
                        'uid': form.get('uid'),
                        'name': form.get('name'),
                        'asset_type': form.get('asset_type'),
                        'deployment_active': form.get('deployment__active', False),
                        'submission_count': form.get('deployment__submission_count', 0),
                        'date_created': form.get('date_created'),
                        'date_modified': form.get('date_modified'),
                        'url': form.get('url'),
                        'settings': form.get('settings', {})
                    }
                    formatted_forms.append(form_data)

                return self.success_response(
                    data=formatted_forms,
                    metadata={
                        'total_forms': len(formatted_forms),
                        'kobo_server': kobo_service.server_url,
                        'fetched_at': datetime.utcnow().isoformat()
                    }
                )

            except Exception as e:
                return self.error_response(f"Failed to fetch Kobo forms: {str(e)}")

        except Exception as e:
            logger.error(f"Error in get_kobo_forms: {e}", exc_info=True)
            return self.error_response(f"Failed to get Kobo forms: {str(e)}")

    def handle_sync_kobo_responses(self, params: Dict, user=None) -> MCPResponse:
        """
        Sync responses from KoboToolbox for a specific assessment

        Args:
            params: Request parameters with assessment_id
            user: Authenticated user (required)

        Returns:
            MCPResponse with sync results
        """
        try:
            if not user:
                return self.error_response("Authentication required for Kobo sync")

            assessment_id = params.get('assessment_id')
            if not assessment_id:
                return self.error_response("assessment_id parameter is required")

            # Check permissions
            if not self.check_permissions(user, 'write', 'assessments'):
                return self.error_response("Insufficient permissions to sync Kobo data")

            # Get assessment
            try:
                assessment = Assessment.objects.get(id=assessment_id)
            except Assessment.DoesNotExist:
                return self.error_response(f"Assessment with ID {assessment_id} not found")

            if not assessment.kobo_form_id:
                return self.error_response("Assessment does not have a Kobo form ID configured")

            # Get Kobo service
            try:
                kobo_service = get_kobo_service_for_user(user)
            except Exception as e:
                return self.error_response(f"Kobo integration not configured: {str(e)}")

            # Sync responses
            try:
                # Get submissions from Kobo
                submissions = kobo_service.get_form_submissions(assessment.kobo_form_id)

                sync_results = {
                    'total_submissions': len(submissions),
                    'new_responses': 0,
                    'updated_responses': 0,
                    'errors': []
                }

                # Process each submission
                for submission in submissions:
                    try:
                        submission_id = submission.get('_uuid') or submission.get('_id')
                        if not submission_id:
                            continue

                        # Try to find existing response
                        response, created = AssessmentResponse.objects.get_or_create(
                            assessment=assessment,
                            kobo_submission_id=submission_id,
                            defaults={
                                'kobo_data': submission,
                                'is_submitted': True,
                                'submitted_at': datetime.utcnow(),
                                'respondent': user,  # Default to sync user
                                'site_id': assessment.target_sites.first().id if assessment.target_sites.exists() else None
                            }
                        )

                        if created:
                            sync_results['new_responses'] += 1
                        else:
                            # Update existing response
                            response.kobo_data = submission
                            response.updated_at = datetime.utcnow()
                            response.save()
                            sync_results['updated_responses'] += 1

                    except Exception as e:
                        sync_results['errors'].append(f"Error processing submission {submission_id}: {str(e)}")

                # Update assessment status if needed
                if assessment.status == 'draft' and sync_results['new_responses'] > 0:
                    assessment.status = 'active'
                    assessment.save()

                sync_results['sync_completed_at'] = datetime.utcnow().isoformat()

                return self.success_response(data=sync_results)

            except Exception as e:
                return self.error_response(f"Failed to sync Kobo responses: {str(e)}")

        except Exception as e:
            logger.error(f"Error in sync_kobo_responses: {e}", exc_info=True)
            return self.error_response(f"Failed to sync responses: {str(e)}")

    def _apply_assessment_filters(self, queryset, params: Dict):
        """Apply assessment-specific filters to queryset"""

        # Filter by site
        if params.get('site_id'):
            queryset = queryset.filter(target_sites__id=params['site_id'])

        # Filter by status
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])

        # Filter by assessment type
        if params.get('assessment_type'):
            queryset = queryset.filter(assessment_type=params['assessment_type'])

        # Filter by Kobo form ID
        if params.get('kobo_form_id'):
            queryset = queryset.filter(kobo_form_id=params['kobo_form_id'])

        # Filter by assigned user
        if params.get('assigned_to'):
            queryset = queryset.filter(assigned_to__id=params['assigned_to'])

        # Filter by creator
        if params.get('created_by'):
            queryset = queryset.filter(created_by__id=params['created_by'])

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

        # Filter by assessment period
        if params.get('assessment_from_date'):
            try:
                from_date = datetime.strptime(params['assessment_from_date'], '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__gte=from_date)
            except ValueError:
                logger.warning("Invalid assessment_from_date format")

        if params.get('assessment_to_date'):
            try:
                to_date = datetime.strptime(params['assessment_to_date'], '%Y-%m-%d').date()
                queryset = queryset.filter(end_date__lte=to_date)
            except ValueError:
                logger.warning("Invalid assessment_to_date format")

        return queryset

    def _serialize_assessment(self, assessment: Assessment, include_responses_summary: bool = False,
                            include_sites: bool = False, include_responses_data: bool = False,
                            full_details: bool = False) -> Dict:
        """
        Serialize Assessment model to dictionary

        Args:
            assessment: Assessment model instance
            include_responses_summary: Include responses summary
            include_sites: Include target sites data
            include_responses_data: Include full responses data
            full_details: Include all available details

        Returns:
            Serialized assessment data
        """
        data = {
            'id': assessment.id,
            'title': assessment.title,
            'title_ar': assessment.title_ar,
            'description': assessment.description,
            'assessment_type': assessment.assessment_type,
            'assessment_type_display': assessment.get_assessment_type_display(),
            'status': assessment.status,
            'status_display': assessment.get_status_display(),
            'is_active': assessment.is_active,
            'response_count': assessment.response_count,
            'kobo_form_id': assessment.kobo_form_id,
            'kobo_form_url': assessment.kobo_form_url,
            'start_date': assessment.start_date.isoformat() if assessment.start_date else None,
            'end_date': assessment.end_date.isoformat() if assessment.end_date else None,
            'created_at': assessment.created_at.isoformat(),
            'updated_at': assessment.updated_at.isoformat()
        }

        # Creator information
        if assessment.created_by:
            data['created_by'] = {
                'id': assessment.created_by.id,
                'username': assessment.created_by.username,
                'full_name': f"{assessment.created_by.first_name} {assessment.created_by.last_name}".strip()
            }

        # Assigned users
        if full_details:
            assigned_users = []
            for user in assessment.assigned_to.all():
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'full_name': f"{user.first_name} {user.last_name}".strip()
                }
                assigned_users.append(user_data)
            data['assigned_to'] = assigned_users

        # Target sites
        if include_sites:
            sites = []
            for site in assessment.target_sites.all():
                site_data = {
                    'id': site.id,
                    'name': site.name,
                    'name_ar': site.name_ar,
                    'site_type': site.site_type,
                    'operational_status': site.operational_status,
                    'total_population': site.total_population,
                    'coordinates': site.coordinates
                }
                sites.append(site_data)
            data['target_sites'] = sites

        # Responses summary
        if include_responses_summary:
            responses = assessment.responses.all()
            if responses:
                submitted_count = responses.filter(is_submitted=True).count()
                latest_response = responses.order_by('-submitted_at').first()

                data['responses_summary'] = {
                    'total_responses': len(responses),
                    'submitted_responses': submitted_count,
                    'draft_responses': len(responses) - submitted_count,
                    'completion_rate': (submitted_count / len(responses) * 100) if responses else 0,
                    'latest_response_at': latest_response.submitted_at.isoformat() if latest_response and latest_response.submitted_at else None,
                    'sites_with_responses': responses.values('site').distinct().count()
                }

        # Full responses data
        if include_responses_data:
            responses_data = []
            for response in assessment.responses.all():
                response_data = {
                    'id': response.id,
                    'kobo_submission_id': response.kobo_submission_id,
                    'is_submitted': response.is_submitted,
                    'submitted_at': response.submitted_at.isoformat() if response.submitted_at else None,
                    'site': {
                        'id': response.site.id if response.site else None,
                        'name': response.site.name if response.site else None
                    },
                    'respondent': {
                        'id': response.respondent.id,
                        'username': response.respondent.username
                    },
                    'gps_location': response.gps_location,
                    'kobo_data': response.kobo_data if full_details else None
                }
                responses_data.append(response_data)
            data['responses'] = responses_data

        return data

    def _generate_assessment_summary(self, assessment: Assessment) -> Dict:
        """Generate summary analysis for assessment"""
        responses = assessment.responses.filter(is_submitted=True)

        summary = {
            'total_sites_targeted': assessment.target_sites.count(),
            'total_responses': responses.count(),
            'sites_with_responses': responses.values('site').distinct().count(),
            'coverage_percentage': 0,
            'response_timeline': [],
            'key_statistics': {}
        }

        if assessment.target_sites.count() > 0:
            summary['coverage_percentage'] = (
                summary['sites_with_responses'] / assessment.target_sites.count() * 100
            )

        # Response timeline (by day)
        if responses.exists():
            timeline_data = responses.extra(
                select={'date': 'DATE(submitted_at)'}
            ).values('date').annotate(count=Count('id')).order_by('date')

            summary['response_timeline'] = [
                {
                    'date': item['date'].isoformat() if item['date'] else None,
                    'responses': item['count']
                }
                for item in timeline_data
            ]

        return summary

    def _generate_trend_analysis(self, assessment: Assessment) -> Dict:
        """Generate trend analysis for assessment"""
        # This would analyze trends in the Kobo data
        # For now, return placeholder structure
        return {
            'temporal_trends': [],
            'geographic_trends': [],
            'thematic_trends': [],
            'analysis_note': "Detailed trend analysis requires specific indicator mapping"
        }

    def _generate_comparison_analysis(self, assessment: Assessment, compare_with: List[int]) -> Dict:
        """Generate comparison analysis with other assessments"""
        comparison_assessments = Assessment.objects.filter(id__in=compare_with)

        comparison_data = {
            'base_assessment': {
                'id': assessment.id,
                'title': assessment.title,
                'response_count': assessment.response_count
            },
            'compared_assessments': [],
            'comparative_metrics': {}
        }

        for comp_assessment in comparison_assessments:
            comp_data = {
                'id': comp_assessment.id,
                'title': comp_assessment.title,
                'response_count': comp_assessment.response_count,
                'status': comp_assessment.status
            }
            comparison_data['compared_assessments'].append(comp_data)

        return comparison_data

    def _extract_key_indicators(self, assessment: Assessment) -> Dict:
        """Extract key humanitarian indicators from assessment responses"""
        # This would analyze the Kobo response data to extract key indicators
        # Implementation would depend on the specific form structure
        return {
            'demographic_indicators': {},
            'needs_indicators': {},
            'service_indicators': {},
            'vulnerability_indicators': {},
            'analysis_note': "Specific indicators depend on assessment form structure"
        }


# Create server instance
assessments_server = AssessmentsMCPServer()