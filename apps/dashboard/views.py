from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.assessments.models import Assessment
from apps.sites.models import Site
from apps.accounts.models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """Get dashboard overview data"""
    user = request.user
    
    # Get user's assessments
    if user.is_staff or user.role in ['admin', 'cluster_lead']:
        assessments = Assessment.objects.all()
        sites = Site.objects.all()
    else:
        assessments = Assessment.objects.filter(
            models.Q(created_by=user) | models.Q(assigned_to=user)
        ).distinct()
        # For regular users, show only sites they have assessments for
        sites = Site.objects.filter(assessments__in=assessments).distinct()
    
    # Filter active assessments
    active_assessments = assessments.filter(status='active')
    
    data = {
        'total_assessments': assessments.count(),
        'active_assessments': active_assessments.count(),
        'total_sites': sites.count(),
        'recent_assessments': [
            {
                'id': a.id,
                'title': a.title,
                'assessment_type': a.assessment_type,
                'status': a.status,
                'response_count': a.response_count,
                'created_at': a.created_at
            } for a in assessments.order_by('-created_at')[:5]
        ]
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assessment_dashboard_data(request):
    """Get assessment-specific dashboard data"""
    user = request.user
    
    # Get user's assessments
    if user.is_staff or user.role in ['admin', 'cluster_lead']:
        assessments = Assessment.objects.all()
    else:
        assessments = Assessment.objects.filter(
            models.Q(created_by=user) | models.Q(assigned_to=user)
        ).distinct()
    
    # Get assessments by status
    status_counts = {}
    for status_choice in Assessment.STATUS_CHOICES:
        status_key = status_choice[0]
        count = assessments.filter(status=status_key).count()
        status_counts[status_key] = count
    
    # Get assessments by type
    type_counts = {}
    for type_choice in Assessment.ASSESSMENT_TYPES:
        type_key = type_choice[0]
        count = assessments.filter(assessment_type=type_key).count()
        type_counts[type_key] = count
    
    # Get assessments ready to launch (active assessments with Kobo forms)
    ready_to_launch = assessments.filter(
        status='active',
        kobo_form_id__isnull=False
    ).exclude(kobo_form_id='')
    
    data = {
        'status_counts': status_counts,
        'type_counts': type_counts,
        'ready_to_launch': [
            {
                'id': a.id,
                'title': a.title,
                'assessment_type': a.assessment_type,
                'target_sites_count': a.target_sites.count(),
                'response_count': a.response_count
            } for a in ready_to_launch
        ]
    }
    
    return Response(data)


@login_required
def dashboard_home(request):
    """Main dashboard view"""
    context = {
        'user': request.user,
        'page_title': 'Dashboard'
    }
    return render(request, 'dashboard/home.html', context)
