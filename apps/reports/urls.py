from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FieldReportViewSet, ReportAnalysisViewSet, ReportTagViewSet
from .test_views import test_reports_endpoint

app_name = 'reports'

router = DefaultRouter()
router.register(r'field-reports', FieldReportViewSet, basename='fieldreport')
router.register(r'analyses', ReportAnalysisViewSet, basename='reportanalysis')
router.register(r'tags', ReportTagViewSet, basename='reporttag')

urlpatterns = [
    path('test/', test_reports_endpoint, name='test'),
    path('', include(router.urls)),
]