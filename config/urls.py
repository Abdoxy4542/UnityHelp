# ===== config/urls.py =====
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    # Temporarily disable endpoints for apps without urls modules
    # path('api/v1/sites/', include('apps.sites.urls')),
    # path('api/v1/reports/', include('apps.reports.urls')),
    # path('api/v1/assessments/', include('apps.assessments.urls')),
    # path('api/v1/alerts/', include('apps.alerts.urls')),
    # path('api/v1/integrations/', include('apps.integrations.urls')),
    # path('api/v1/dashboard/', include('apps.dashboard.urls')),
    
    # Web dashboard
    # path('', include('apps.dashboard.web_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
