from django.urls import path
from . import views

urlpatterns = [
    # Dashboard home
    path('', views.dashboard_home, name='dashboard-home'),
    
    # API endpoints
    path('api/overview/', views.dashboard_overview, name='dashboard-overview'),
    path('api/assessments/', views.assessment_dashboard_data, name='assessment-dashboard-data'),
]