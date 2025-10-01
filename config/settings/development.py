# ===== config/settings/development.py =====
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '10.0.2.2', '*']

# Development database: Flexible SQLite/PostGIS configuration
USE_POSTGIS = env('USE_POSTGIS', default=False, cast=bool)

if USE_POSTGIS:
    # PostGIS with PostgreSQL (when available)
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': env('DB_NAME', default='unityaid_db'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default='postgres'),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }
else:
    # SQLite for development (with limited GIS support)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# GIS Configuration
import os
import site

# Configure GDAL/GEOS library paths for Windows
OSGEO_PATH = os.path.join(site.getsitepackages()[1], 'osgeo')
GDAL_LIBRARY_PATH = os.path.join(OSGEO_PATH, 'gdal.dll')
GEOS_LIBRARY_PATH = os.path.join(OSGEO_PATH, 'geos_c.dll')

# Add to PATH so DLLs can be found
if OSGEO_PATH not in os.environ.get('PATH', ''):
    os.environ['PATH'] = OSGEO_PATH + os.pathsep + os.environ.get('PATH', '')

# Set GDAL data directory
os.environ['GDAL_DATA'] = os.path.join(OSGEO_PATH, 'data', 'gdal')
os.environ['PROJ_LIB'] = os.path.join(OSGEO_PATH, 'data', 'proj')

# Use simple cache instead of Redis for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable Celery for development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React Native dev
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Email backend for development - using console for now
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Email configuration (for production, you can switch to SMTP)
DEFAULT_FROM_EMAIL = 'UnityAid Platform <noreply@unityaid.com>'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# For development, show emails in console instead of sending
# To use real email, change EMAIL_BACKEND to:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Override REST Framework settings for easier development testing
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow anonymous access in development
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}