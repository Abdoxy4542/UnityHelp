from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Authentication routes
router.register(r'auth/devices', views.DeviceViewSet, basename='device')

# Core app routes
router.register(r'sites', views.SiteViewSet, basename='mobile-site')
router.register(r'assessments', views.AssessmentViewSet, basename='mobile-assessment')
router.register(r'assessment-responses', views.AssessmentResponseViewSet, basename='mobile-assessment-response')
router.register(r'field-reports', views.MobileFieldReportViewSet, basename='mobile-field-report')
router.register(r'dashboard', views.DashboardViewSet, basename='mobile-dashboard')

app_name = 'mobile_api_v1'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.MobileLoginView.as_view(), name='mobile-login'),
    path('auth/register/', views.MobileRegisterView.as_view(), name='mobile-register'),
    path('auth/refresh/', views.RefreshTokenView.as_view(), name='refresh-token'),
    path('auth/logout/', views.MobileLogoutView.as_view(), name='mobile-logout'),
    path('auth/profile/', views.MobileProfileView.as_view(), name='mobile-profile'),
    path('auth/password-reset/', views.MobilePasswordResetView.as_view(), name='mobile-password-reset'),
    path('auth/verify-email/', views.MobileVerifyEmailView.as_view(), name='mobile-verify-email'),

    # Sync endpoints
    path('sync/initial/', views.InitialSyncView.as_view(), name='initial-sync'),
    path('sync/incremental/', views.IncrementalSyncView.as_view(), name='incremental-sync'),
    path('sync/bulk-upload/', views.BulkUploadView.as_view(), name='bulk-upload'),

    # Health check
    path('health/', views.HealthCheckView.as_view(), name='health-check'),

    # Include router URLs
    path('', include(router.urls)),
]