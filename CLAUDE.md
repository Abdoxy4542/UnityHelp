# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UnityAid is an AI-powered humanitarian platform built with Django and React that helps aid organizations manage operations, collect data, and generate insights. The platform supports multiple user roles including GSOs (Gathering Site Officials), NGO users, UN users, cluster leads, and admins.

## Architecture

### Backend (Django)
- **Django 5.2.5** with Django REST Framework
- **PostGIS/PostgreSQL** database with geographic data support
- **Redis** for caching and Celery task queue
- **Celery** for background task processing
- **Channels** for WebSocket/real-time functionality
- **Modular app structure** following Django best practices

### Frontend (React)
- **React 19** with Redux Toolkit for state management
- **Mapbox GL** for geographic visualization
- **Axios** for API communication
- Located in `frontend/` directory

### Key Django Apps
- `apps/accounts/` - Custom user authentication with role-based permissions
- `apps/sites/` - Site management for humanitarian locations
- `apps/assessments/` - Survey/assessment creation and data collection
- `apps/reports/` - Data analysis and report generation
- `apps/dashboard/` - Main user interface and metrics
- `apps/alerts/` - Alert system management
- `apps/integrations/` - External service integrations (HDX, KoboToolbox)

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
DB_NAME=unityaid_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379
```

### Settings Structure
- `config/settings/base.py` - Base configuration
- `config/settings/development.py` - Development settings
- `config/settings/production.py` - Production settings
- Default: `config.settings.development`

### Database Requirements
- **PostgreSQL 12+** with **PostGIS** extension
- Database name: `unityaid_db`
- The custom User model is in `apps.accounts.User`

## Key Models & Architecture Decisions

### Custom User Model
- Located in `apps/accounts/models.py`
- Extends `AbstractUser` with role-based permissions
- Roles: GSO, NGO User, UN User, Cluster Lead, Admin, Public User
- Includes location field for geographic data
- Multi-language support (English/Arabic)

### Geographic Data
- Uses PostGIS for spatial data
- Location stored as GeoJSON format in development
- Ready for production PostGIS deployment

### API Documentation
- **drf-spectacular** for OpenAPI documentation
- Available at `/api/docs/` when server is running
- Schema endpoint: `/api/schema/`

## Testing & Code Quality

### Current State
- Test framework: Django's built-in testing
- No specific linting configuration found
- Frontend uses React Testing Library and Jest

### Recommended Commands
```bash
# Run Django tests
python manage.py test

# Run frontend tests
cd frontend && npm test

# For production deployments, ensure to:
python manage.py check --deploy
```

## Deployment Notes

- Project includes `deployment/` directory structure
- Supports Docker and Kubernetes configurations
- Uses `logs/django.log` for application logging
- Static files served from `staticfiles/`
- Media files in `media/`

## Common Development Patterns

### Adding New Apps
1. Create app: `python manage.py startapp app_name apps/app_name`
2. Add to `LOCAL_APPS` in `config/settings/base.py`
3. Create URLs and include in `config/urls.py`
4. Run migrations if models added

### API Development
- Use Django REST Framework
- Token and Session authentication configured
- Pagination set to 20 items per page
- Filter, search, and ordering backends enabled

### Internationalization
- Supports English and Arabic
- Timezone: Africa/Khartoum
- Locale files in `locale/` directory