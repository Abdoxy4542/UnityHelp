# ===== config/settings/development.py =====
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development database: use SQLite locally to avoid PostGIS requirement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Remove GIS-related apps in development to avoid GDAL/GEOS requirements
INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app not in (
        'django.contrib.gis',
        'rest_framework_gis',
    )
]

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React Native dev
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'