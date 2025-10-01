# UnityAid Mobile API

## Overview

The UnityAid Mobile API is a comprehensive RESTful API designed specifically for mobile applications operating in humanitarian aid environments. It provides robust offline capabilities, efficient data synchronization, and role-based access control suitable for challenging field conditions.

## Features

### 🔐 Advanced Authentication
- Token-based authentication with refresh tokens
- Device registration and management
- Role-based access control (GSO, NGO, UN, Admin)
- Secure logout with token revocation

### 📱 Mobile-Optimized Endpoints
- **Sites Management**: CRUD operations with GPS integration
- **Assessments**: Kobo integration and offline form management
- **Data Sync**: Initial and incremental synchronization
- **Bulk Operations**: Offline data upload capabilities
- **Dashboard**: Real-time metrics and activity feeds

### 🚀 Performance & Reliability
- Redis caching for improved response times
- Database query optimization
- Pagination and filtering
- Rate limiting and security middleware
- Comprehensive error handling

### 📊 Monitoring & Logging
- Request/response logging
- Performance monitoring
- API health checks
- Usage analytics

## Quick Start

### 1. Installation

The mobile API is automatically included when you install the UnityAid platform:

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### 2. API Endpoints

Base URL: `/api/mobile/v1/`

#### Authentication
```
POST /auth/login/          # Mobile login
POST /auth/register/       # User registration
POST /auth/refresh/        # Refresh access token
POST /auth/logout/         # Logout
GET  /auth/profile/        # Get user profile
PATCH /auth/profile/       # Update profile
```

#### Sites
```
GET    /sites/             # List sites
POST   /sites/             # Create site
GET    /sites/{id}/        # Get site details
PATCH  /sites/{id}/        # Update site
GET    /sites/nearby/      # Get nearby sites
GET    /sites/summary/     # Get sites statistics
```

#### Assessments
```
GET    /assessments/                    # List assessments
GET    /assessments/my_assignments/     # Get my assignments
GET    /assessments/{id}/form_data/     # Get form data
```

#### Assessment Responses
```
GET    /assessment-responses/           # List my responses
POST   /assessment-responses/           # Create response
PATCH  /assessment-responses/{id}/      # Update response
POST   /assessment-responses/{id}/submit/ # Submit response
GET    /assessment-responses/drafts/    # Get draft responses
```

#### Data Synchronization
```
POST   /sync/initial/        # Initial data sync
POST   /sync/incremental/    # Incremental sync
POST   /sync/bulk-upload/    # Bulk data upload
```

#### Device Management
```
GET    /auth/devices/                      # List devices
POST   /auth/devices/{id}/update_fcm_token/ # Update FCM token
```

### 3. Authentication Flow

```javascript
// Login
const loginResponse = await fetch('/api/mobile/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
    device_id: 'unique_device_id',
    platform: 'android'
  })
});

const { access_token, refresh_token } = await loginResponse.json();

// Use access token for API calls
const sitesResponse = await fetch('/api/mobile/v1/sites/', {
  headers: { 'Authorization': `Token ${access_token}` }
});
```

## Architecture

### Models

#### MobileDevice
- Tracks registered mobile devices
- Stores device metadata (platform, version, FCM token)
- Links to user accounts

#### RefreshToken
- Manages refresh tokens for authentication
- Automatic expiry and cleanup
- Device-specific tokens

#### SyncLog
- Tracks synchronization operations
- Performance monitoring
- Error tracking and recovery

### Serializers

Mobile-optimized serializers that:
- Reduce bandwidth usage
- Include computed fields (population summaries, coordinates)
- Support nested relationships
- Validate GPS coordinates and data integrity

### ViewSets

Comprehensive ViewSets with:
- Role-based filtering
- Performance optimization (select_related, prefetch_related)
- Caching integration
- Mobile-specific actions (nearby sites, form data)

## Testing

### Running Tests

```bash
# Run all mobile API tests
python manage.py test apps.mobile_api

# Run specific test modules
python manage.py test apps.mobile_api.tests.test_authentication
python manage.py test apps.mobile_api.tests.test_sites
python manage.py test apps.mobile_api.tests.test_sync

# Run performance tests
python manage.py test apps.mobile_api.tests.test_performance

# Run integration tests
python manage.py test apps.mobile_api.tests.test_integration
```

### Test Coverage

- **Unit Tests**: Individual endpoint functionality
- **Integration Tests**: Cross-app workflows
- **Performance Tests**: Load testing and optimization
- **Security Tests**: Authentication and authorization
- **Mobile-Specific Tests**: GPS validation, offline sync

## Configuration

### Settings

Add mobile API middleware to Django settings:

```python
MIDDLEWARE = [
    # ... other middleware
    'apps.mobile_api.middleware.MobileAPILoggingMiddleware',
    'apps.mobile_api.middleware.MobileAPISecurityMiddleware',
    'apps.mobile_api.middleware.MobileAPIMonitoringMiddleware',
]

# Mobile API specific settings
MOBILE_API = {
    'PAGINATION_SIZE': 20,
    'MAX_SYNC_ITEMS': 100,
    'TOKEN_EXPIRY_HOURS': 24,
    'REFRESH_TOKEN_EXPIRY_DAYS': 30,
    'RATE_LIMIT_PER_MINUTE': 100,
}
```

### Caching

Configure Redis for optimal performance:

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

### Logging

Configure logging for monitoring:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mobile_api_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/mobile_api.log',
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

## Mobile App Integration

### Best Practices

1. **Authentication Management**
   - Store tokens securely (Keychain/Keystore)
   - Implement automatic refresh
   - Handle logout cleanup

2. **Offline Support**
   - Cache essential data locally
   - Queue operations for later sync
   - Handle conflict resolution

3. **Data Synchronization**
   - Use incremental sync for efficiency
   - Implement retry mechanisms
   - Show sync progress to users

4. **Error Handling**
   - Graceful network error handling
   - User-friendly error messages
   - Retry strategies for failed requests

5. **Performance**
   - Implement lazy loading
   - Use pagination effectively
   - Cache frequently accessed data

### Sample Integration Code

#### React Native Example

```javascript
class UnityAidAPI {
  constructor() {
    this.baseURL = 'https://your-domain.com/api/mobile/v1';
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
```

## Security

### Authentication
- JWT-like token system with refresh capability
- Device binding for enhanced security
- Automatic token rotation

### Authorization
- Role-based access control (RBAC)
- Field-level permissions
- Site-based access restrictions

### Data Protection
- HTTPS enforcement
- Input validation and sanitization
- SQL injection prevention
- XSS protection

### Rate Limiting
- IP-based rate limiting
- User-based quotas
- Endpoint-specific limits

## Monitoring

### Health Checks

```bash
# Check API health
curl /api/mobile/v1/health/

# Response
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

### Metrics

The API automatically tracks:
- Request/response times
- Error rates by endpoint
- User activity patterns
- Sync operation success rates

### Alerts

Configure alerts for:
- High error rates (>10%)
- Slow response times (>2s)
- Failed sync operations
- Authentication failures

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Check token expiry
   - Verify device registration
   - Ensure proper header format

2. **Sync Failures**
   - Check network connectivity
   - Verify data format
   - Review sync logs

3. **Performance Issues**
   - Enable Redis caching
   - Check database indices
   - Monitor query performance

### Debug Mode

Enable debug logging:

```python
LOGGING['loggers']['mobile_api']['level'] = 'DEBUG'
```

### Support

- **Documentation**: Full API documentation available
- **Tests**: Comprehensive test suite for validation
- **Monitoring**: Built-in health checks and metrics
- **Logging**: Detailed request/response logging

## Contributing

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Follow security best practices

## License

This mobile API is part of the UnityAid platform and follows the same licensing terms.