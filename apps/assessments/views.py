from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Assessment, AssessmentResponse, KoboIntegrationSettings
from .serializers import (
    AssessmentSerializer, AssessmentListSerializer, AssessmentResponseSerializer,
    KoboIntegrationSettingsSerializer, KoboFormSerializer, AssessmentLaunchSerializer
)
from apps.sites.models import Site
from apps.integrations.kobo_service import get_kobo_service_for_user, KoboAPIService
import logging

logger = logging.getLogger(__name__)


class AssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing assessments"""
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['admin', 'cluster_lead']:
            return Assessment.objects.all()
        else:
            # Users can see assessments they created or are assigned to
            return Assessment.objects.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        return AssessmentSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an assessment"""
        assessment = self.get_object()
        assessment.status = 'active'
        assessment.save()
        return Response({'status': 'Assessment activated'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete an assessment"""
        assessment = self.get_object()
        assessment.status = 'completed'
        assessment.save()
        return Response({'status': 'Assessment completed'})
    
    @action(detail=True, methods=['get'])
    def launch_url(self, request, pk=None):
        """Get launch URL for assessment"""
        assessment = self.get_object()
        site_id = request.query_params.get('site_id')
        
        try:
            kobo_service = get_kobo_service_for_user(request.user)
            
            if assessment.kobo_form_id:
                form_url = kobo_service.get_form_url(assessment.kobo_form_id)
                
                if site_id:
                    site = get_object_or_404(Site, id=site_id)
                    form_url += f"?site_id={site.id}&site_name={site.name}"
                
                return Response({
                    'launch_url': form_url,
                    'assessment_id': assessment.id,
                    'assessment_title': assessment.title
                })
            else:
                return Response(
                    {'error': 'No Kobo form linked to this assessment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AssessmentResponseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing assessment responses"""
    serializer_class = AssessmentResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = AssessmentResponse.objects.all()
        
        # Filter by assessment if provided
        assessment_id = self.request.query_params.get('assessment')
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        
        # Filter by site if provided
        site_id = self.request.query_params.get('site')
        if site_id:
            queryset = queryset.filter(site_id=site_id)
        
        # Non-admin users can only see their own responses
        if not (user.is_staff or user.role in ['admin', 'cluster_lead']):
            queryset = queryset.filter(respondent=user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(respondent=self.request.user)


class KoboIntegrationSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Kobo integration settings"""
    serializer_class = KoboIntegrationSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return KoboIntegrationSettings.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test Kobo API connection"""
        settings = self.get_object()
        
        try:
            kobo_service = KoboAPIService(
                server_url=settings.kobo_server_url,
                username=settings.kobo_username,
                api_token=settings.kobo_api_token
            )
            
            if kobo_service.test_connection():
                return Response({'status': 'Connection successful'})
            else:
                return Response(
                    {'error': 'Connection failed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kobo_forms_list(request):
    """Get list of available Kobo forms for the user"""
    try:
        kobo_service = get_kobo_service_for_user(request.user)
        forms = kobo_service.get_assets()
        
        # Filter only survey assets
        survey_forms = [form for form in forms if form.get('asset_type') == 'survey']
        
        serializer = KoboFormSerializer(survey_forms, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Failed to fetch Kobo forms for user {request.user.id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_kobo_submissions(request, assessment_id):
    """Sync submissions from Kobo for a specific assessment"""
    try:
        assessment = get_object_or_404(Assessment, id=assessment_id)
        
        # Check if user has permission
        if not (request.user == assessment.created_by or 
                request.user in assessment.assigned_to.all() or
                request.user.is_staff):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not assessment.kobo_form_id:
            return Response(
                {'error': 'No Kobo form linked to this assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        kobo_service = get_kobo_service_for_user(request.user)
        submissions = kobo_service.get_form_submissions(assessment.kobo_form_id)
        
        synced_count = 0
        for submission_data in submissions:
            submission_id = submission_data.get('_id')
            
            # Check if submission already exists
            if not AssessmentResponse.objects.filter(
                assessment=assessment,
                kobo_submission_id=submission_id
            ).exists():
                
                # Try to match site from submission data
                site = None
                site_id = submission_data.get('site_id')
                if site_id:
                    try:
                        site = Site.objects.get(id=site_id)
                    except Site.DoesNotExist:
                        pass
                
                # Create response record
                AssessmentResponse.objects.create(
                    assessment=assessment,
                    site=site,
                    respondent=request.user,  # This should ideally match the actual respondent
                    kobo_submission_id=submission_id,
                    kobo_data=submission_data,
                    is_submitted=True,
                    submitted_at=timezone.now()
                )
                synced_count += 1
        
        return Response({
            'message': f'Synced {synced_count} new submissions',
            'synced_count': synced_count,
            'total_submissions': len(submissions)
        })
        
    except Exception as e:
        logger.error(f"Failed to sync submissions for assessment {assessment_id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_kobo_connection(request):
    """Test Kobo API connection for the current user"""
    try:
        kobo_service = get_kobo_service_for_user(request.user)
        
        if kobo_service.test_connection():
            return Response({'status': 'Connection successful'})
        else:
            return Response(
                {'error': 'Connection failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_assessment_to_sites(request, assessment_id):
    """Send assessment to gathering site mobile apps"""
    try:
        assessment = get_object_or_404(Assessment, id=assessment_id)

        # Check if user has permission to send assessments
        if not (request.user == assessment.created_by or
                request.user.is_staff or
                request.user.role in ['admin', 'cluster_lead']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not assessment.kobo_form_id:
            return Response(
                {'error': 'No Kobo form linked to this assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get selected sites from request
        site_ids = request.data.get('site_ids', [])
        if not site_ids:
            # If no specific sites selected, use all target sites
            sites = assessment.target_sites.all()
        else:
            sites = Site.objects.filter(id__in=site_ids)

        if not sites:
            return Response(
                {'error': 'No sites selected for assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update assessment status to active
        assessment.status = 'active'
        assessment.save()

        # Here you would implement the mobile app notification system
        # For now, we'll create assessment response records to track
        sent_count = 0
        for site in sites:
            # Create assessment response record for tracking
            assessment_response, created = AssessmentResponse.objects.get_or_create(
                assessment=assessment,
                site=site,
                respondent=request.user,  # Will be updated when GSO responds
                defaults={
                    'is_submitted': False,
                    'gps_location': site.location
                }
            )
            if created:
                sent_count += 1

        # TODO: Implement push notification to mobile app
        # - Send push notification to GSOs at selected sites
        # - Include assessment details and Kobo form URL
        # - Track delivery status

        return Response({
            'message': f'Assessment sent to {sent_count} gathering sites',
            'assessment_id': assessment.id,
            'sites_notified': [{'id': s.id, 'name': s.name} for s in sites],
            'kobo_form_url': assessment.kobo_form_url,
            'status': 'Assessment activated and sent to mobile apps'
        })

    except Exception as e:
        logger.error(f"Failed to send assessment {assessment_id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@login_required
def assessment_creation_page(request):
    """Assessment creation page for dashboard users"""
    context = {
        'user': request.user,
        'page_title': 'Create Assessment'
    }
    return render(request, 'assessments/create_assessment.html', context)


@login_required
def kobo_settings_page(request):
    """Kobo settings configuration page"""
    context = {
        'user': request.user,
        'page_title': 'Kobo Integration Settings'
    }
    return render(request, 'assessments/kobo_settings.html', context)


@login_required
def launch_assessment_for_site(request, assessment_id, site_id):
    """Launch assessment form for a specific site"""
    try:
        assessment = get_object_or_404(Assessment, id=assessment_id)
        site = get_object_or_404(Site, id=site_id)
        
        # Check if user has permission
        if not (request.user == assessment.created_by or 
                request.user in assessment.assigned_to.all() or
                request.user.is_staff):
            return JsonResponse(
                {'error': 'Permission denied'},
                status=403
            )
        
        if not assessment.kobo_form_id:
            return JsonResponse(
                {'error': 'No Kobo form linked to this assessment'},
                status=400
            )
        
        kobo_service = get_kobo_service_for_user(request.user)
        form_url = kobo_service.get_form_url(assessment.kobo_form_id)
        
        # Add context to form URL
        form_url += f"?user_id={request.user.id}&assessment_id={assessment.id}&site_id={site.id}&site_name={site.name}"
        
        if request.GET.get('ajax'):
            return JsonResponse({
                'launch_url': form_url,
                'site_name': site.name,
                'assessment_title': assessment.title
            })
        else:
            return HttpResponseRedirect(form_url)
            
    except Exception as e:
        logger.error(f"Failed to launch assessment {assessment_id} for site {site_id}: {e}")
        if request.GET.get('ajax'):
            return JsonResponse({'error': str(e)}, status=400)
        else:
            return render(request, 'assessments/error.html', {'error': str(e)})
