"""
Configuration settings for UnityAid MCP Servers
"""

import os
from pathlib import Path
from decouple import config

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DJANGO_BASE_DIR = BASE_DIR.parent

# Django settings
DJANGO_SETTINGS_MODULE = config('DJANGO_SETTINGS_MODULE', default='config.settings.development')

# Database settings (from Django settings)
DATABASE_CONFIG = {
    'NAME': config('DB_NAME', default='unityaid_db'),
    'USER': config('DB_USER', default='postgres'),
    'PASSWORD': config('DB_PASSWORD', default=''),
    'HOST': config('DB_HOST', default='localhost'),
    'PORT': config('DB_PORT', default='5432', cast=int),
}

# Redis settings
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')

# MCP Server settings
MCP_SERVER_CONFIG = {
    'name': 'unityaid-mcp',
    'version': '1.0.0',
    'description': 'UnityAid Humanitarian Platform MCP Server',
    'author': 'UnityAid Team',
    'capabilities': [
        'tools',
        'resources',
        'prompts'
    ]
}

# API settings
API_CONFIG = {
    'base_url': config('API_BASE_URL', default='http://localhost:8000/api/v1/'),
    'timeout': config('API_TIMEOUT', default=30, cast=int),
    'max_retries': config('API_MAX_RETRIES', default=3, cast=int)
}

# Authentication settings
AUTH_CONFIG = {
    'token_expiry': config('TOKEN_EXPIRY', default=3600, cast=int),  # 1 hour
    'refresh_token_expiry': config('REFRESH_TOKEN_EXPIRY', default=86400, cast=int),  # 24 hours
    'secret_key': config('SECRET_KEY', default='your-secret-key-here')
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': DJANGO_BASE_DIR / 'logs' / 'mcp_server.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'mcp_server': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# External service configurations
EXTERNAL_SERVICES = {
    'hdx': {
        'base_url': config('HDX_BASE_URL', default='https://data.humdata.org/api/3/'),
        'api_key': config('HDX_API_KEY', default=''),
        'timeout': 60
    },
    'kobo': {
        'base_url': config('KOBO_BASE_URL', default='https://kobocat.org/api/v1/'),
        'token': config('KOBO_TOKEN', default=''),
        'timeout': 30
    }
}

# Data validation schemas
VALIDATION_SCHEMAS = {
    'site': {
        'required_fields': ['name', 'location', 'site_type'],
        'optional_fields': ['description', 'capacity', 'facilities']
    },
    'report': {
        'required_fields': ['title', 'report_type', 'data_sources'],
        'optional_fields': ['description', 'parameters', 'schedule']
    },
    'assessment': {
        'required_fields': ['title', 'assessment_type', 'questions'],
        'optional_fields': ['description', 'target_sites', 'deadline']
    }
}

# Rate limiting
RATE_LIMIT_CONFIG = {
    'enabled': config('RATE_LIMIT_ENABLED', default=True, cast=bool),
    'requests_per_minute': config('RATE_LIMIT_RPM', default=60, cast=int),
    'requests_per_hour': config('RATE_LIMIT_RPH', default=1000, cast=int)
}

# Cache settings
CACHE_CONFIG = {
    'enabled': config('CACHE_ENABLED', default=True, cast=bool),
    'ttl': config('CACHE_TTL', default=300, cast=int),  # 5 minutes
    'prefix': 'unityaid_mcp'
}

# Export formats
SUPPORTED_EXPORT_FORMATS = {
    'reports': ['pdf', 'xlsx', 'csv', 'json'],
    'assessments': ['xlsx', 'csv', 'json'],
    'sites': ['geojson', 'csv', 'json']
}

# Pagination defaults
PAGINATION_CONFIG = {
    'default_page_size': 20,
    'max_page_size': 100
}

def get_django_settings():
    """Get Django settings for database access"""
    import sys
    import django
    from django.conf import settings

    # Add Django project to path
    sys.path.append(str(DJANGO_BASE_DIR))

    # Configure Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)

    if not settings.configured:
        django.setup()

    return settings

def validate_config():
    """Validate configuration settings"""
    errors = []

    # Check required database settings
    if not DATABASE_CONFIG['NAME']:
        errors.append("Database name is required")

    if not DATABASE_CONFIG['USER']:
        errors.append("Database user is required")

    # Check external service configurations
    if EXTERNAL_SERVICES['hdx']['api_key'] and not EXTERNAL_SERVICES['hdx']['base_url']:
        errors.append("HDX base URL is required when API key is provided")

    if EXTERNAL_SERVICES['kobo']['token'] and not EXTERNAL_SERVICES['kobo']['base_url']:
        errors.append("Kobo base URL is required when token is provided")

    if errors:
        raise ValueError("Configuration errors: " + ", ".join(errors))

    return True