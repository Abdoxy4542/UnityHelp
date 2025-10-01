from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SudanCrisisDataViewSet, DataIntegrationViewSet, HumanitarianActionPlanViewSet

app_name = 'integrations'

router = DefaultRouter()
router.register(r'crisis-data', SudanCrisisDataViewSet, basename='crisis-data')
router.register(r'humanitarian-action-plans', HumanitarianActionPlanViewSet, basename='humanitarian-action-plans')
router.register(r'data-integration', DataIntegrationViewSet, basename='data-integration')

urlpatterns = [
    path('api/', include(router.urls)),
]