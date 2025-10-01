# UnityAid Mobile API Integration Documentation

## Overview

This document provides comprehensive documentation for the UnityAid Mobile API integration, which connects all Django apps with mobile applications through a robust, production-ready RESTful API.

## 🎯 Integration Summary

The mobile API successfully integrates the following Django apps:
- **Accounts** - User authentication and management
- **Sites** - Humanitarian site management
- **Assessments** - Data collection and surveys
- **Reports** - Analytics and reporting
- **Mobile API** - Mobile-optimized endpoints and synchronization

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Endpoints](#api-endpoints)
3. [Authentication & Security](#authentication--security)
4. [Data Synchronization](#data-synchronization)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Guide](#deployment-guide)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile Apps   │◄──►│   Mobile API    │◄──►│  Django Apps    │
│                 │    │   (REST API)    │    │                 │
│ - iOS App       │    │                 │    │ - Sites         │
│ - Android App   │    │ - Authentication│    │ - Assessments   │
│ - React Native  │    │ - Synchronization│   │ - Accounts      │
│ - PWA           │    │ - Offline Support│   │ - Reports       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌───────▼────────┐
                       │   Database     │
                       │ (PostgreSQL)   │
                       └────────────────┘
```

### Core Components

1. **Mobile API Layer** (`apps/mobile_api/`)
   - RESTful API endpoints optimized for mobile usage
   - Token-based authentication with refresh capability
   - Data synchronization and offline support
   - Role-based access control

2. **Integration Layer**
   - Seamless connection between mobile API and Django apps
   - Bidirectional data flow validation
   - Cross-app workflow support

3. **Security Layer**
   - JWT-like authentication system
   - Device registration and management
   - Input validation and sanitization
   - Rate limiting and DDoS protection

### Data Flow

```
Mobile App Request → Authentication → Authorization → Business Logic → Database → Response
     ▲                                                                              │
     └──────────────────── Sync/Offline Data ◄─────────────────────────────────────┘
```

## 🔌 API Endpoints

### Base URL
```
Production: https://your-domain.com/api/mobile/v1/
Development: http://localhost:8000/api/mobile/v1/
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | User login with device registration |
| POST | `/auth/register/` | User registration |
| POST | `/auth/refresh/` | Refresh access token |
| POST | `/auth/logout/` | Logout and invalidate tokens |
| GET | `/auth/profile/` | Get user profile |
| PATCH | `/auth/profile/` | Update user profile |

### Sites Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sites/` | List sites (role-based filtering) |
| POST | `/sites/` | Create new site |
| GET | `/sites/{id}/` | Get site details |
| PATCH | `/sites/{id}/` | Update site |
| DELETE | `/sites/{id}/` | Delete site |
| GET | `/sites/nearby/` | Get nearby sites (GPS-based) |
| GET | `/sites/summary/` | Get sites statistics |

### Assessments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/assessments/` | List assessments |
| GET | `/assessments/my_assignments/` | Get user's assigned assessments |
| GET | `/assessments/{id}/form_data/` | Get assessment form structure |

### Assessment Responses

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/assessment-responses/` | List user's responses |
| POST | `/assessment-responses/` | Create new response |
| PATCH | `/assessment-responses/{id}/` | Update response |
| POST | `/assessment-responses/{id}/submit/` | Submit response |
| GET | `/assessment-responses/drafts/` | Get draft responses |

### Data Synchronization

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/initial/` | Initial data synchronization |
| POST | `/sync/incremental/` | Incremental sync since last update |
| POST | `/sync/bulk-upload/` | Bulk upload offline data |

### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/devices/` | List user devices |
| POST | `/auth/devices/{id}/update_fcm_token/` | Update FCM token |

## 🔐 Authentication & Security

### Authentication Flow

1. **Initial Login**
   ```json
   POST /api/mobile/v1/auth/login/
   {
     "email": "user@example.com",
     "password": "password123",
     "device_id": "unique_device_id",
     "platform": "android"
   }
   ```

2. **Response**
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
     "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
     "token_type": "Bearer",
     "expires_in": 86400,
     "user": {
       "id": 123,
       "email": "user@example.com",
       "role": "gso",
       "organization": "NGO Name"
     }
   }
   ```

3. **Authenticated Requests**
   ```
   Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGci...
   ```

### Security Features

- **Token-based Authentication**: JWT-like tokens with device binding
- **Refresh Token Rotation**: Automatic token refresh for security
- **Device Registration**: Track and limit concurrent sessions
- **Role-based Access Control**: Fine-grained permissions by user role
- **Input Validation**: Comprehensive data validation and sanitization
- **Rate Limiting**: Protection against brute force and DDoS attacks
- **HTTPS Enforcement**: Secure communication in production

### User Roles and Permissions

| Role | Permissions |
|------|-------------|
| **GSO** | Manage assigned sites, create/update assessments, view organization data |
| **NGO User** | View organization sites, submit assessments, limited data access |
| **UN User** | Regional data access, cross-organization visibility |
| **Cluster Lead** | Area-wide data access, coordination capabilities |
| **Admin** | Full system access, user management, system configuration |

## 🔄 Data Synchronization

### Sync Types

1. **Initial Sync**: Complete data download for first-time users
2. **Incremental Sync**: Updates since last synchronization
3. **Bulk Upload**: Offline data upload when connectivity restored

### Sync Process

```javascript
// Initial Sync
const syncData = {
  data_types: ['sites', 'assessments'],
  last_sync: null
};

const response = await fetch('/api/mobile/v1/sync/initial/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(syncData)
});

const result = await response.json();
// Returns: { sites: [...], assessments: [...], sync_timestamp: "..." }
```

### Offline Data Handling

```javascript
// Bulk Upload Offline Data
const offlineData = {
  sites: [
    {
      temp_id: 'offline_site_1',
      name: 'Offline Created Site',
      // ... other site data
      created_offline: true,
      offline_timestamp: '2024-01-15T10:30:00Z'
    }
  ]
};

const uploadResponse = await fetch('/api/mobile/v1/sync/bulk-upload/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(offlineData)
});

const uploadResult = await uploadResponse.json();
// Returns: { sites_created: 1, site_mappings: { offline_site_1: 123 } }
```

## 🧪 Testing Strategy

### Test Coverage Overview

The mobile API includes comprehensive test coverage across multiple dimensions:

#### 1. Integration Tests
- **Django → Mobile API** (`test_django_to_mobile_integration.py`)
  - Verifies Django app data is accessible via mobile API
  - Tests user role changes and data visibility
  - Validates cross-app data relationships

- **Mobile API → Django** (`test_mobile_to_django_integration.py`)
  - Verifies mobile API data persists correctly in Django
  - Tests bulk operations and data validation
  - Validates bidirectional data consistency

#### 2. Workflow Tests
- **Cross-app Workflows** (`test_cross_app_workflows.py`)
  - Complete user journeys from login to data collection
  - Multi-role collaboration scenarios
  - Offline-to-online workflow validation

#### 3. Production-Grade Tests
- **Security Tests** (`test_security_production.py`)
  - Authentication and authorization validation
  - Input validation and XSS protection
  - Rate limiting and brute force protection

- **Performance Tests** (`test_performance_production.py`)
  - Response time validation (<2s for list endpoints)
  - Database query optimization verification
  - Concurrent access performance testing

- **Data Consistency** (`test_data_consistency.py`)
  - Transaction integrity validation
  - Concurrent update handling
  - Cross-operation data consistency

#### 4. Deployment Verification
- **Deployment Tests** (`test_deployment_verification.py`)
  - Configuration validation
  - Health check endpoints
  - Production readiness verification

### Running Tests

```bash
# Run all mobile API tests
python manage.py test apps.mobile_api

# Run specific test categories
python manage.py test apps.mobile_api.tests.test_django_to_mobile_integration
python manage.py test apps.mobile_api.tests.test_security_production
python manage.py test apps.mobile_api.tests.test_performance_production

# Run deployment verification
python manage.py test apps.mobile_api.tests.test_deployment_verification

# Coverage report
coverage run --source='apps.mobile_api' manage.py test apps.mobile_api
coverage report
coverage html
```

## 🚀 Deployment Guide

### Prerequisites

1. **System Requirements**
   - Python 3.8+
   - PostgreSQL 12+ with PostGIS
   - Redis 6+
   - SSL certificate for HTTPS

2. **Environment Variables**
   ```env
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com

   # Database
   DB_NAME=unityaid_production
   DB_USER=unityaid_user
   DB_PASSWORD=secure_password
   DB_HOST=localhost
   DB_PORT=5432

   # Redis
   REDIS_URL=redis://localhost:6379/1

   # Security
   SECURE_SSL_REDIRECT=True
   SECURE_HSTS_SECONDS=31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS=True
   SECURE_CONTENT_TYPE_NOSNIFF=True
   SECURE_BROWSER_XSS_FILTER=True
   ```

### Deployment Steps

1. **Database Setup**
   ```bash
   # Create database
   createdb unityaid_production

   # Run migrations
   python manage.py migrate

   # Create superuser
   python manage.py createsuperuser
   ```

2. **Static Files**
   ```bash
   # Collect static files
   python manage.py collectstatic --noinput
   ```

3. **Security Check**
   ```bash
   # Run security check
   python manage.py check --deploy
   ```

4. **Test Deployment**
   ```bash
   # Run deployment verification tests
   python apps/mobile_api/tests/test_deployment_verification.py
   ```

5. **Start Services**
   ```bash
   # Web server (Gunicorn)
   gunicorn config.wsgi:application --bind 0.0.0.0:8000

   # Background workers (Celery)
   celery -A config worker --loglevel=info

   # Task scheduler (Celery Beat)
   celery -A config beat --loglevel=info
   ```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:pass@db:5432/unityaid
    depends_on:
      - db
      - redis

  db:
    image: postgis/postgis:13-3.1
    environment:
      - POSTGRES_DB=unityaid
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## ⚡ Performance Optimization

### Database Optimization

1. **Query Optimization**
   ```python
   # Use select_related and prefetch_related
   sites = Site.objects.select_related(
       'state', 'locality', 'site_type', 'organization'
   ).prefetch_related(
       'assigned_gsos', 'facilities'
   )
   ```

2. **Database Indexes**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['status', 'created_at']),
           models.Index(fields=['state', 'locality']),
           models.Index(fields=['organization']),
       ]
   ```

### Caching Strategy

1. **Redis Configuration**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   ```

2. **View-level Caching**
   ```python
   from django.core.cache import cache

   def get_sites_summary(self, request):
       cache_key = f'sites_summary_{request.user.role}'
       summary = cache.get(cache_key)

       if not summary:
           summary = self.calculate_summary()
           cache.set(cache_key, summary, 300)  # 5 minutes

       return Response(summary)
   ```

### Mobile Optimization

1. **Response Size Optimization**
   - Paginated responses (20 items per page)
   - Minimal field serialization for list views
   - Compressed responses (gzip)

2. **Bandwidth Efficiency**
   - Delta sync for incremental updates
   - Image compression and resizing
   - Optional field inclusion based on client needs

## 📊 Monitoring & Maintenance

### Health Checks

1. **API Health Endpoint**
   ```bash
   curl https://your-domain.com/api/mobile/v1/health/
   ```

   Response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-15T10:30:00Z",
     "database": "healthy",
     "cache": "healthy",
     "services": {
       "api": "healthy",
       "authentication": "healthy"
     }
   }
   ```

2. **Database Health**
   ```bash
   python manage.py dbshell -c "SELECT 1;"
   ```

3. **Cache Health**
   ```bash
   redis-cli ping
   ```

### Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'mobile_api_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/mobile_api.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'mobile_api': {
            'handlers': ['mobile_api_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Monitoring Metrics

Track these key metrics:

1. **API Performance**
   - Response times (p50, p95, p99)
   - Error rates by endpoint
   - Request volume patterns

2. **Authentication**
   - Login success/failure rates
   - Token refresh frequency
   - Concurrent session counts

3. **Data Synchronization**
   - Sync operation success rates
   - Sync data volume
   - Offline usage patterns

4. **System Resources**
   - Database connection pool usage
   - Redis memory usage
   - CPU and memory utilization

### Alerts Configuration

Set up alerts for:
- API response time > 5 seconds
- Error rate > 5%
- Database connection failures
- Failed sync operations > 10%
- High memory usage > 85%

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Problems

**Symptom**: Users cannot log in or tokens expire unexpectedly

**Solutions**:
```bash
# Check token expiration settings
python manage.py shell
>>> from apps.mobile_api.models import RefreshToken
>>> RefreshToken.objects.filter(is_active=True).count()

# Clear expired tokens
python manage.py mobile_api_cleanup_tokens
```

#### 2. Sync Failures

**Symptom**: Data synchronization fails or returns partial data

**Solutions**:
```bash
# Check sync logs
python manage.py shell
>>> from apps.mobile_api.models import SyncLog
>>> SyncLog.objects.filter(status='failed').order_by('-created_at')[:10]

# Verify database constraints
python manage.py check
```

#### 3. Performance Issues

**Symptom**: Slow API responses

**Solutions**:
```bash
# Check database query performance
python manage.py shell
>>> from django.db import connection
>>> print(connection.queries)

# Monitor Redis performance
redis-cli --latency-history

# Check for N+1 queries
python manage.py shell
>>> from django.conf import settings
>>> settings.DEBUG = True  # Enable query logging
```

#### 4. Permission Errors

**Symptom**: Users cannot access expected data

**Solutions**:
```python
# Debug user permissions
from apps.accounts.models import User
user = User.objects.get(email='user@example.com')
print(f"Role: {user.role}")
print(f"Organization: {user.organization}")
print(f"Active: {user.is_active}")

# Check site assignments
from apps.sites.models import Site
sites = Site.objects.filter(assigned_gsos=user)
print(f"Assigned sites: {sites.count()}")
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
# settings/development.py
LOGGING['loggers']['mobile_api']['level'] = 'DEBUG'

# Enable SQL query logging
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
```

### Performance Profiling

```bash
# Install django-debug-toolbar for development
pip install django-debug-toolbar

# Add to INSTALLED_APPS and MIDDLEWARE
# Access profiling at /__debug__/

# Profile specific endpoints
python manage.py shell
>>> import cProfile
>>> cProfile.run('api_call_here')
```

## 📚 API Client Examples

### React Native Integration

```javascript
// api/unityaid.js
class UnityAidAPI {
  constructor(baseURL = 'https://your-domain.com/api/mobile/v1') {
    this.baseURL = baseURL;
    this.token = null;
  }

  async login(credentials) {
    const response = await fetch(`${this.baseURL}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });

    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
      await this.storeTokens(data);
      return data;
    }
    throw new Error('Login failed');
  }

  async getSites(params = {}) {
    return this.apiCall('/sites/', { method: 'GET', params });
  }

  async createSite(siteData) {
    return this.apiCall('/sites/', { method: 'POST', body: siteData });
  }

  async syncData(dataTypes = ['sites', 'assessments']) {
    return this.apiCall('/sync/initial/', {
      method: 'POST',
      body: { data_types: dataTypes }
    });
  }

  async apiCall(endpoint, options = {}) {
    const url = new URL(endpoint, this.baseURL);

    if (options.params) {
      Object.keys(options.params).forEach(key =>
        url.searchParams.append(key, options.params[key])
      );
    }

    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${this.token}`
      }
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    const response = await fetch(url.toString(), config);

    if (response.status === 401) {
      await this.refreshToken();
      return this.apiCall(endpoint, options); // Retry
    }

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return response.json();
  }
}

export default UnityAidAPI;
```

### Flutter/Dart Integration

```dart
// lib/services/unity_aid_api.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class UnityAidAPI {
  final String baseURL;
  String? _token;

  UnityAidAPI({this.baseURL = 'https://your-domain.com/api/mobile/v1'});

  Future<Map<String, dynamic>> login(Map<String, dynamic> credentials) async {
    final response = await http.post(
      Uri.parse('$baseURL/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(credentials),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _token = data['access_token'];
      return data;
    }
    throw Exception('Login failed');
  }

  Future<List<dynamic>> getSites() async {
    return await _apiCall('/sites/');
  }

  Future<Map<String, dynamic>> createSite(Map<String, dynamic> siteData) async {
    return await _apiCall('/sites/', method: 'POST', body: siteData);
  }

  Future<dynamic> _apiCall(String endpoint, {
    String method = 'GET',
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('$baseURL$endpoint');
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token $_token',
    };

    http.Response response;
    switch (method) {
      case 'POST':
        response = await http.post(uri, headers: headers, body: jsonEncode(body));
        break;
      case 'PATCH':
        response = await http.patch(uri, headers: headers, body: jsonEncode(body));
        break;
      default:
        response = await http.get(uri, headers: headers);
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    }
    throw Exception('API call failed: ${response.statusCode}');
  }
}
```

## 📈 Roadmap & Future Enhancements

### Phase 1: Current Implementation ✅
- Django app integration
- Mobile API endpoints
- Authentication system
- Data synchronization
- Production-grade testing

### Phase 2: Advanced Features (Future)
- Real-time notifications (WebSocket)
- Advanced offline capabilities
- Enhanced geospatial features
- Multi-language support enhancement
- Advanced analytics dashboard

### Phase 3: Scalability (Future)
- Microservices architecture
- API rate limiting enhancements
- Advanced caching strategies
- Database sharding
- CDN integration

## 🤝 Contributing

### Development Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/unityaid-platform.git
   cd unityaid-platform
   ```

2. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py loaddata fixtures/test_data.json
   ```

4. **Run Tests**
   ```bash
   python manage.py test apps.mobile_api
   ```

### Code Standards

- Follow PEP 8 for Python code
- Use Django best practices
- Write comprehensive tests for new features
- Document API changes in this file
- Use semantic commit messages

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Run full test suite
4. Update documentation
5. Submit pull request with description

## 📞 Support

### Documentation
- API Documentation: `/api/docs/` (when server running)
- Django Admin: `/admin/`
- This Integration Guide

### Contact
- Technical Issues: [GitHub Issues](https://github.com/your-org/unityaid-platform/issues)
- Security Issues: security@unityaid.org
- General Questions: support@unityaid.org

### Resources
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [Mobile API Best Practices](https://docs.unityaid.org/mobile-api/)
- [Authentication Guide](https://docs.unityaid.org/auth/)

---

## ✅ Integration Verification Checklist

Use this checklist to verify successful integration:

### Backend Integration
- [ ] All Django apps properly connected to Mobile API
- [ ] Authentication system working with all user roles
- [ ] Data synchronization functioning bidirectionally
- [ ] All test suites passing (500+ tests)
- [ ] Security measures implemented and tested
- [ ] Performance benchmarks met

### Mobile Integration
- [ ] Mobile apps can authenticate successfully
- [ ] Data CRUD operations working through API
- [ ] Offline synchronization functioning
- [ ] Role-based data access enforced
- [ ] Error handling graceful and informative

### Production Readiness
- [ ] Configuration validated for production
- [ ] Security settings enabled
- [ ] Monitoring and logging configured
- [ ] Performance optimization applied
- [ ] Deployment verification tests passing

### Documentation
- [ ] API endpoints documented
- [ ] Integration guide complete
- [ ] Troubleshooting guide available
- [ ] Client examples provided

---

**🎉 The UnityAid Mobile API integration is now complete and production-ready!**

This integration provides a robust, secure, and scalable foundation for mobile applications in humanitarian environments, with comprehensive testing, monitoring, and documentation to ensure long-term success.