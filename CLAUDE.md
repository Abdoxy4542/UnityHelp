# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UnityAid is an AI-powered humanitarian platform built with Django and React that helps aid organizations manage operations, collect data, and generate insights. The platform supports multiple user roles including GSOs (Gathering Site Officials), NGO users, UN users, cluster leads, and admins.

## Architecture

### Backend (Django)
- **Django 5.2.5** with Django REST Framework
- **Flexible database**: SQLite (development) or PostGIS/PostgreSQL (production) with geographic data support
- **Redis** for caching and Celery task queue (production), local memory cache (development)
- **Celery** for background task processing (disabled in development)
- **Channels** with Redis for WebSocket/real-time functionality
- **Modular app structure** following Django best practices

### Frontend (React)
- **React 19** with Redux Toolkit for state management
- **Mapbox GL** for geographic visualization
- **Axios** for API communication
- Located in `frontend/` directory
- Redux store includes: sites, alerts, and filters slices

### Key Django Apps
- `apps/accounts/` - Custom user authentication with role-based permissions, email verification, password reset
- `apps/sites/` - Site management for humanitarian locations with State/Locality/Site hierarchy
- `apps/assessments/` - Survey/assessment creation with Kobo integration and data collection
- `apps/reports/` - Data analysis and report generation
- `apps/integrations/` - External service integrations (HDX, KoboToolbox, DTM, UNHCR, FTS, Humanitarian Action)
- `apps/mobile_api/` - Mobile-specific API endpoints
- `apps/ai/` - AI-powered features and models
- `apps/mcp_servers/` - MCP server integration

## Development Commands

### Backend (Django)
```bash
# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database operations
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Create migrations
python manage.py makemigrations

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Frontend (React)
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Background Services
```bash
# Start Celery worker
celery -A config worker --loglevel=info

# Start Celery beat scheduler
celery -A config beat --loglevel=info
```

## Configuration

### Environment Variables
The project uses `python-decouple` for environment management. Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database (optional - defaults to SQLite in development)
USE_POSTGIS=False  # Set to True to use PostgreSQL with PostGIS
DB_NAME=unityaid_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Redis (only needed in production)
REDIS_URL=redis://localhost:6379

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

### Settings Structure
- `config/settings/base.py` - Base configuration (includes GDAL availability check)
- `config/settings/development.py` - Development settings (SQLite default, local cache, Celery disabled)
- `config/settings/production.py` - Production settings (PostGIS, Redis required)
- Default settings module: `config.settings.development` (set in `manage.py`)
- ASGI configuration in `config/asgi.py` includes WebSocket routing
- Celery configuration in `config/celery.py`

### Database Requirements
- **Development**: SQLite (default) or PostgreSQL with PostGIS (set `USE_POSTGIS=True`)
- **Production**: PostgreSQL 12+ with PostGIS extension required
- Database name: `unityaid_db`
- The custom User model is `apps.accounts.User` (set via `AUTH_USER_MODEL`)

## Key Models & Architecture Decisions

### Custom User Model (`apps/accounts/models.py`)
- Extends `AbstractUser` with role-based permissions
- **Roles**: `gso`, `ngo_user`, `un_user`, `cluster_lead`, `admin`, `public`
- **Additional fields**: organization, phone_number, location (JSONField), preferred_language, is_verified
- **Related models**: UserProfile (avatar, bio, notification preferences), EmailVerification, PasswordReset
- **ManyToMany**: `assigned_sites` relationship with Site model

### Geographic Data Model
- **Hierarchical structure**: State → Locality → Site
- All geographic models store location as **JSONField** with GeoJSON format: `{"type": "Point", "coordinates": [lon, lat]}`
- Site model includes extensive demographics (population, age groups, gender, vulnerability indicators)
- Site includes calculated properties: `average_household_size`, `vulnerability_rate`, `child_dependency_ratio`
- Ready for PostGIS migration when `USE_POSTGIS=True`

### Assessment & Data Collection
- **Assessment model**: Links to Kobo forms via `kobo_form_id` and `kobo_form_url`
- **AssessmentResponse**: Stores submissions with `kobo_submission_id` and raw `kobo_data` (JSONField)
- **KoboIntegrationSettings**: User-specific Kobo API configuration per user
- Supports offline data collection with GPS location tracking

### External Integrations (`apps/integrations/`)
- Service modules for: HDX, KoboToolbox, DTM, UNHCR, FTS, Humanitarian Action
- Each service has dedicated module in `apps/integrations/` directory

### WebSocket/Real-time Features
- Channels configured with Redis backend for WebSocket support
- WebSocket routing defined in `apps.dashboard.routing`
- ASGI application configured in `config/asgi.py`

### API Architecture
- **URL structure**: `/api/v1/{app_name}/` for standard APIs, `/api/mobile/` for mobile-specific endpoints
- **Authentication**: Token and Session authentication (Token preferred for mobile)
- **Documentation**: drf-spectacular at `/api/docs/` (Swagger UI) and `/api/schema/` (OpenAPI schema)
- **Permissions**: `AllowAny` in development, `IsAuthenticated` in production
- **Pagination**: 20 items per page with filter/search/ordering support

## Testing & Code Quality

### Django Tests
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test apps.accounts

# Run with verbosity
python manage.py test --verbosity=2

# Check for deployment issues
python manage.py check --deploy
```

### Frontend Tests
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

## Common Development Patterns

### Adding New Apps
1. Create app: `python manage.py startapp app_name apps/app_name`
2. Add to `LOCAL_APPS` in `config/settings/base.py` (around line 64)
3. Create `urls.py` in app and include in `config/urls.py`
4. Create migrations: `python manage.py makemigrations app_name`
5. Apply migrations: `python manage.py migrate`

### Working with Geographic Data
- Use JSONField for location data in development: `{"type": "Point", "coordinates": [lon, lat]}`
- Access coordinates via model properties: `site.longitude`, `site.latitude`, `site.coordinates`
- For PostGIS: Set `USE_POSTGIS=True` and use `PointField` from `django.contrib.gis.db.models`

### Kobo Integration Pattern
1. Create/link Assessment with `kobo_form_id`
2. Store submissions as AssessmentResponse with `kobo_data` JSONField
3. Use KoboIntegrationSettings for per-user API credentials
4. Service module at `apps/integrations/kobo_service.py`

### Frontend State Management
- Redux store configured in `frontend/src/app/store.js`
- Create slices in `frontend/src/features/{feature}/` directory
- API calls via axios instance in `frontend/src/services/api.js`
- Base URL: `/api` (proxied to Django backend)

### Internationalization
- Supports English (`en`) and Arabic (`ar`)
- Timezone: `Africa/Khartoum`
- Use `gettext_lazy` for model strings
- Locale files in `locale/` directory
- Many models have `name` and `name_ar` fields for bilingual support

### Email in Development
- Emails printed to console by default (`EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`)
- Switch to SMTP backend in production
- Used for: email verification codes, password reset codes

### Logging
- Configured to log to both console and `logs/django.log`
- Verbose format includes: levelname, timestamp, module, process, thread, message
- Level: INFO

### Static and Media Files
- Static files: Collected to `staticfiles/` via `python manage.py collectstatic`
- Media uploads: Stored in `media/` directory
- Profile images: `media/profile_images/`