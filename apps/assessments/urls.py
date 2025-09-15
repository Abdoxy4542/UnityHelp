from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('assessments', views.AssessmentViewSet, basename='assessment')
router.register('responses', views.AssessmentResponseViewSet, basename='assessment-response')
router.register('kobo-settings', views.KoboIntegrationSettingsViewSet, basename='kobo-settings')

urlpatterns = [
    # API routes
    path('', include(router.urls)),

    # Assessment creation and management
    path('create/', views.assessment_creation_page, name='create-assessment-page'),
    path('kobo-settings/', views.kobo_settings_page, name='kobo-settings-page'),
    path('assessments/<int:assessment_id>/send-to-sites/', views.send_assessment_to_sites, name='send-assessment-to-sites'),

    # Kobo integration endpoints
    path('kobo/forms/', views.kobo_forms_list, name='kobo-forms'),
    path('kobo/sync/<int:assessment_id>/', views.sync_kobo_submissions, name='sync-kobo-submissions'),
    path('kobo/test-connection/', views.test_kobo_connection, name='test-kobo-connection'),
]