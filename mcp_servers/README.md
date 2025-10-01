# UnityAid MCP Servers

Model Context Protocol (MCP) servers for the UnityAid humanitarian platform. These servers provide programmatic access to UnityAid's core functionality including site management, report generation, assessment tools, and external integrations.

## Overview

The UnityAid MCP servers expose the platform's capabilities through standardized MCP tools, allowing AI assistants and other clients to interact with humanitarian data and operations programmatically.

### Available Servers

1. **Main Server** (`main.py`) - Unified server with all functionality
2. **Sites Server** (`sites_server.py`) - Site and location management
3. **Reports Server** (`reports_server.py`) - Report generation and analytics
4. **Assessments Server** (`assessments_server.py`) - Assessment creation and data collection
5. **Integrations Server** (`integrations_server.py`) - External service integrations

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Django is properly configured and the database is accessible.

3. Set up environment variables in your `.env` file:
```env
DJANGO_SETTINGS_MODULE=config.settings.development
DB_NAME=unityaid_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## Running the Server

### Quick Start
```bash
python run_server.py
```

### Development Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python run_server.py
```

### Individual Servers
You can also run individual servers for specific functionality:
```bash
python -m sites_server
python -m reports_server
python -m assessments_server
python -m integrations_server
```

## Available Tools

### Site Management
- `list_sites` - List humanitarian sites with filtering
- `get_site_details` - Get detailed site information
- `create_site` - Create new sites
- `update_site` - Update existing sites
- `get_sites_by_region` - Filter sites by geographic region

### Report Generation
- `list_reports` - List reports with filtering options
- `get_report_details` - Get detailed report information
- `create_report` - Create new reports
- `generate_report` - Generate/compile reports
- `export_report` - Export reports in various formats
- `get_report_analytics` - Get report usage analytics

### Assessment Management
- `list_assessments` - List assessments with filtering
- `get_assessment_details` - Get detailed assessment information
- `create_assessment` - Create new assessments
- `update_assessment` - Update existing assessments
- `submit_assessment_response` - Submit assessment responses
- `get_assessment_analytics` - Get assessment analytics

### External Integrations
- `list_integrations` - List configured integrations
- `get_integration_status` - Check integration status
- `sync_with_hdx` - Synchronize with Humanitarian Data Exchange
- `sync_with_kobo` - Synchronize with KoboToolbox
- `export_to_hdx` - Export data to HDX
- `configure_integration` - Set up new integrations
- `test_integration` - Test integration connectivity

### System Tools
- `get_system_status` - Get overall system health and status

## Configuration

The servers use `config.py` for configuration management. Key settings include:

- **Database Configuration**: Connection details for PostgreSQL/PostGIS
- **External Services**: API keys and endpoints for HDX, Kobo, etc.
- **Authentication**: Token management and security settings
- **Rate Limiting**: API rate limiting configuration
- **Caching**: Redis cache configuration
- **Logging**: Structured logging setup

## Data Formats

### Geographic Data
Sites and locations use GeoJSON format:
```json
{
  "type": "Point",
  "coordinates": [longitude, latitude]
}
```

### Timestamps
All timestamps are in ISO 8601 format with timezone information:
```json
"2024-01-15T14:30:00Z"
```

### Response Format
All tools return responses in a consistent format:
```json
{
  "success": true,
  "data": {...},
  "metadata": {
    "timestamp": "2024-01-15T14:30:00Z",
    "count": 10,
    "pagination": {...}
  }
}
```

## Error Handling

Errors are returned in a standardized format:
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {...}
}
```

## Security

- All API calls require authentication
- Rate limiting is enforced
- Input validation is performed on all parameters
- Database queries use parameterized statements

## Development

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/test_sites_server.py
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .
```

## Monitoring

The servers include comprehensive logging and can be monitored through:
- Log files in `logs/mcp_server.log`
- System status endpoint
- Database connection health checks

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure PostGIS extension is installed

2. **Django Import Errors**
   - Verify Django settings module is correct
   - Check Python path includes Django project
   - Run `python manage.py check` in main project

3. **External Service Errors**
   - Verify API keys and endpoints
   - Check network connectivity
   - Review service-specific logs

### Debug Mode
Enable debug logging for detailed troubleshooting:
```bash
LOG_LEVEL=DEBUG python run_server.py
```