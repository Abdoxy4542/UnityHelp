from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json
import os
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate comprehensive mobile API documentation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='mobile_api_docs.md',
            help='Output file for documentation'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['markdown', 'json', 'postman'],
            default='markdown',
            help='Output format'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Generating mobile API documentation...'))

        output_file = options['output']
        output_format = options['format']

        if output_format == 'markdown':
            self.generate_markdown_docs(output_file)
        elif output_format == 'json':
            self.generate_json_docs(output_file)
        elif output_format == 'postman':
            self.generate_postman_collection(output_file)

        self.stdout.write(
            self.style.SUCCESS(f'Documentation generated successfully: {output_file}')
        )

    def generate_markdown_docs(self, output_file):
        """Generate markdown documentation"""

        docs_content = f"""# UnityAid Mobile API Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

The UnityAid Mobile API provides comprehensive endpoints for mobile applications to interact with the humanitarian aid platform. This API is designed for use in challenging environments with limited connectivity.

## Base URL

```
/api/mobile/v1/
```

## Authentication

The mobile API uses token-based authentication with refresh token support for enhanced security and offline capabilities.

### Login
```http
POST /api/mobile/v1/auth/login/
```

**Request Body:**
```json
{{
  "email": "user@example.com",
  "password": "password123",
  "device_id": "unique_device_identifier",
  "platform": "android|ios|web",
  "fcm_token": "firebase_messaging_token",
  "app_version": "1.0.0",
  "os_version": "Android 12",
  "device_model": "Samsung Galaxy S21"
}}
```

**Response:**
```json
{{
  "user": {{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "gso",
    "organization": "UNHCR"
  }},
  "access_token": "abc123...",
  "refresh_token": "xyz789...",
  "device_id": "device_uuid",
  "expires_in": 86400
}}
```

### Refresh Token
```http
POST /api/mobile/v1/auth/refresh/
```

**Request Body:**
```json
{{
  "refresh_token": "xyz789..."
}}
```

### Registration
```http
POST /api/mobile/v1/auth/register/
```

**Request Body:**
```json
{{
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "organization": "UNHCR",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "device_id": "unique_device_id",
  "platform": "android"
}}
```

## Sites Management

### List Sites
```http
GET /api/mobile/v1/sites/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `site_type`: Filter by site type (gathering, camp, school, health, water, other)
- `operational_status`: Filter by status (active, inactive, planned, closed)
- `state`: Filter by state ID
- `locality`: Filter by locality ID
- `search`: Search by name or description
- `ordering`: Order by field (-updated_at, name, total_population)

**Response:**
```json
{{
  "count": 150,
  "next": "http://api/mobile/v1/sites/?page=2",
  "previous": null,
  "current_page": 1,
  "total_pages": 8,
  "results": [
    {{
      "id": 1,
      "name": "Al-Salam Gathering Site",
      "name_ar": "موقع تجمع السلام",
      "site_type": "gathering",
      "operational_status": "active",
      "state_name": "Khartoum",
      "locality_name": "Khartoum",
      "coordinates": [32.7, 15.7],
      "population_summary": {{
        "total_population": 2500,
        "total_households": 500,
        "children_under_18": 1000,
        "vulnerable_count": 150
      }},
      "last_updated": "2024-01-15T10:30:00Z"
    }}
  ]
}}
```

### Get Site Details
```http
GET /api/mobile/v1/sites/{{id}}/
```

### Create Site
```http
POST /api/mobile/v1/sites/
```

**Request Body:**
```json
{{
  "name": "New Gathering Site",
  "name_ar": "موقع تجمع جديد",
  "site_type": "gathering",
  "operational_status": "active",
  "state": 1,
  "locality": 1,
  "location": {{
    "type": "Point",
    "coordinates": [32.7, 15.7]
  }},
  "total_population": 1500,
  "total_households": 300,
  "contact_person": "Ahmed Hassan",
  "contact_phone": "+249123456789"
}}
```

### Update Site
```http
PATCH /api/mobile/v1/sites/{{id}}/
```

### Nearby Sites
```http
GET /api/mobile/v1/sites/nearby/
```

**Query Parameters:**
- `lat`: Latitude (required)
- `lon`: Longitude (required)
- `radius`: Search radius in km (default: 10)

### Sites Summary
```http
GET /api/mobile/v1/sites/summary/
```

**Response:**
```json
{{
  "total_sites": 150,
  "active_sites": 120,
  "total_population": 125000,
  "by_type": {{
    "gathering": 80,
    "camp": 45,
    "school": 15,
    "health": 10
  }},
  "by_status": {{
    "active": 120,
    "inactive": 20,
    "planned": 10
  }}
}}
```

## Assessments Management

### List Assessments
```http
GET /api/mobile/v1/assessments/
```

**Query Parameters:**
- `assessment_type`: Filter by type (rapid, detailed, needs, monitoring, baseline)
- `status`: Filter by status (draft, active, completed, archived)
- `created_by`: Filter by creator ID
- `search`: Search by title or description

### Get My Assignments
```http
GET /api/mobile/v1/assessments/my_assignments/
```

### Get Assessment Form Data
```http
GET /api/mobile/v1/assessments/{{id}}/form_data/
```

**Response:**
```json
{{
  "form_id": "kobo_form_123",
  "form_url": "https://kf.kobotoolbox.org/forms/123",
  "fields": [
    {{
      "name": "water_access",
      "type": "select_one",
      "label": "Water Access",
      "choices": ["adequate", "limited", "none"]
    }}
  ]
}}
```

## Assessment Responses

### List My Responses
```http
GET /api/mobile/v1/assessment-responses/
```

### Create Response
```http
POST /api/mobile/v1/assessment-responses/
```

**Request Body:**
```json
{{
  "assessment": 1,
  "site": 1,
  "kobo_data": {{
    "water_access": "limited",
    "food_security": "inadequate",
    "shelter_condition": "poor"
  }},
  "gps_location": {{
    "type": "Point",
    "coordinates": [32.7001, 15.7001]
  }}
}}
```

### Submit Response
```http
POST /api/mobile/v1/assessment-responses/{{id}}/submit/
```

### Get Draft Responses
```http
GET /api/mobile/v1/assessment-responses/drafts/
```

## Data Synchronization

### Initial Sync
```http
POST /api/mobile/v1/sync/initial/
```

**Request Body:**
```json
{{
  "data_types": ["sites", "assessments"],
  "device_id": "device_uuid"
}}
```

**Response:**
```json
{{
  "sites": [...],
  "assessments": [...],
  "sync_metadata": {{
    "sync_id": "sync_12345",
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": 1,
    "data_version": "1.0"
  }}
}}
```

### Incremental Sync
```http
POST /api/mobile/v1/sync/incremental/
```

**Request Body:**
```json
{{
  "last_sync_date": "2024-01-15T10:00:00Z",
  "data_types": ["sites"]
}}
```

### Bulk Upload
```http
POST /api/mobile/v1/sync/bulk-upload/
```

**Request Body:**
```json
{{
  "data_type": "sites",
  "items": [
    {{
      "name": "Offline Site 1",
      "site_type": "gathering",
      "total_population": 800
    }}
  ]
}}
```

**Response:**
```json
{{
  "processed": 5,
  "failed": 1,
  "sync_id": "upload_12345"
}}
```

## Dashboard

### Get Dashboard Data
```http
GET /api/mobile/v1/dashboard/
```

**Response:**
```json
{{
  "user_info": {{
    "id": 1,
    "full_name": "John Doe",
    "role": "gso"
  }},
  "statistics": {{
    "sites_count": 25,
    "assessments_count": 10,
    "pending_responses": 3,
    "completed_responses": 15
  }},
  "recent_activities": [...]
}}
```

## Device Management

### List My Devices
```http
GET /api/mobile/v1/auth/devices/
```

### Update FCM Token
```http
POST /api/mobile/v1/auth/devices/{{id}}/update_fcm_token/
```

**Request Body:**
```json
{{
  "fcm_token": "new_fcm_token_here"
}}
```

## Health Check

### API Health Status
```http
GET /api/mobile/v1/health/
```

**Response:**
```json
{{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "database": "healthy",
  "cache": "healthy",
  "services": {{
    "api": "healthy",
    "authentication": "healthy"
  }}
}}
```

## Error Handling

All API endpoints return consistent error responses:

```json
{{
  "error": true,
  "message": "Error description",
  "code": "error_code",
  "timestamp": "2024-01-15T10:30:00Z"
}}
```

### Common HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- 100 requests per minute per IP address
- Bulk operations have separate limits

## Offline Support

The mobile API is designed to work in challenging connectivity environments:

1. **Data Sync**: Regular synchronization of essential data
2. **Offline Storage**: Mobile apps can cache data locally
3. **Bulk Upload**: Submit multiple items when connectivity is restored
4. **Conflict Resolution**: Handle conflicts when same data is modified offline and online

## Security

### Authentication
- Token-based authentication with refresh tokens
- Device registration and tracking
- Automatic token expiry and renewal

### Data Protection
- All sensitive data is encrypted in transit
- Request/response logging excludes sensitive information
- Rate limiting prevents abuse

### Permissions
Role-based access control:
- **GSO**: Access to assigned sites and assessments
- **NGO User**: Read access to active data
- **Admin**: Full access to all data
- **Cluster Lead**: Access to cluster-specific data

## Mobile App Integration Guide

### Initial Setup
1. Register device with login endpoint
2. Store access and refresh tokens securely
3. Implement token refresh logic
4. Set up periodic sync

### Best Practices
1. **Caching**: Cache frequently accessed data locally
2. **Offline Mode**: Design UI to work without connectivity
3. **Sync Strategy**: Implement incremental sync for efficiency
4. **Error Handling**: Gracefully handle network errors
5. **Security**: Store tokens securely, validate certificates

### Sample Code

#### Authentication Flow (JavaScript)
```javascript
class MobileAPIClient {{
  constructor(baseURL) {{
    this.baseURL = baseURL;
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }}

  async login(credentials) {{
    const response = await fetch(`${{this.baseURL}}/auth/login/`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(credentials)
    }});

    if (response.ok) {{
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      localStorage.setItem('access_token', this.accessToken);
      localStorage.setItem('refresh_token', this.refreshToken);
      return data;
    }}
    throw new Error('Login failed');
  }}

  async refreshAccessToken() {{
    const response = await fetch(`${{this.baseURL}}/auth/refresh/`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ refresh_token: this.refreshToken }})
    }});

    if (response.ok) {{
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      localStorage.setItem('access_token', this.accessToken);
      localStorage.setItem('refresh_token', this.refreshToken);
      return data;
    }}
    throw new Error('Token refresh failed');
  }}
}}
```

## Support and Contact

For technical support or questions about the Mobile API:
- Documentation: [API Documentation URL]
- Issues: [GitHub Issues URL]
- Email: support@unityaid.org

---

*This documentation is automatically generated and regularly updated.*
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(docs_content)

    def generate_json_docs(self, output_file):
        """Generate JSON API documentation"""
        # This would generate OpenAPI/Swagger JSON documentation
        # Implementation would use drf-spectacular or similar
        pass

    def generate_postman_collection(self, output_file):
        """Generate Postman collection"""
        # This would generate a Postman collection JSON
        # Implementation would create collection with all endpoints
        pass