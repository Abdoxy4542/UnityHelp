from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .v1 import urls as v1_urls

app_name = 'mobile_api'

urlpatterns = [
    path('v1/', include(v1_urls)),
    # Future API versions can be added here
    # path('v2/', include(v2_urls)),
]