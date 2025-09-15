from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StateViewSet, LocalityViewSet, SiteViewSet

router = DefaultRouter()
router.register(r'states', StateViewSet)
router.register(r'localities', LocalityViewSet)
router.register(r'sites', SiteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]