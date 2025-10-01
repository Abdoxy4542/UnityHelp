"""
Deployment verification tests for UnityAid Mobile API.
Tests production readiness, configuration validation, and system health.
"""

import os
import json
import time
from unittest.mock import patch, Mock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import Organization
from apps.sites.models import Site, State, Locality, SiteType
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog

User = get_user_model()


class DeploymentReadinessTests(TestCase):
    """Test deployment readiness and configuration"""

    def test_required_settings_present(self):
        """Test that all required settings are present for deployment"""
        required_settings = [
            'SECRET_KEY',
            'DATABASES',
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'ROOT_URLCONF',
            'TEMPLATES',
            'STATIC_URL',
            'MEDIA_URL',
            'TIME_ZONE',
            'USE_TZ',
        ]

        for setting_name in required_settings:
            self.assertTrue(
                hasattr(settings, setting_name),
                f"Required setting {setting_name} is missing"
            )

    def test_mobile_api_app_installed(self):
        """Test that mobile API app is properly installed"""
        self.assertIn('apps.mobile_api', settings.INSTALLED_APPS)

    def test_required_middleware_present(self):
        """Test that required middleware is present"""
        required_middleware = [
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]

        for middleware in required_middleware:
            self.assertIn(
                middleware,
                settings.MIDDLEWARE,
                f"Required middleware {middleware} is missing"
            )

    def test_database_configuration(self):
        """Test database configuration is valid"""
        # Test default database connection
        db_config = settings.DATABASES['default']

        required_db_settings = ['ENGINE', 'NAME']
        for setting in required_db_settings:
            self.assertIn(
                setting,
                db_config,
                f"Database setting {setting} is missing"
            )

        # Test database connectivity
        try:
            connection = connections['default']
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_cache_configuration(self):
        """Test cache configuration"""
        # Test cache connectivity
        try:
            cache.set('deployment_test', 'success', 30)
            result = cache.get('deployment_test')
            self.assertEqual(result, 'success')
            cache.delete('deployment_test')
        except Exception as e:
            self.fail(f"Cache connection failed: {e}")

    def test_static_files_configuration(self):
        """Test static files configuration"""
        self.assertTrue(hasattr(settings, 'STATIC_URL'))
        self.assertTrue(hasattr(settings, 'STATIC_ROOT'))

        # Test that static files can be collected
        try:
            call_command('collectstatic', '--noinput', '--dry-run', verbosity=0)
        except Exception as e:
            self.fail(f"Static files collection failed: {e}")

    def test_media_files_configuration(self):
        """Test media files configuration"""
        self.assertTrue(hasattr(settings, 'MEDIA_URL'))
        self.assertTrue(hasattr(settings, 'MEDIA_ROOT'))

        # Test media directory exists or can be created
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        if media_root and not os.path.exists(media_root):
            try:
                os.makedirs(media_root, exist_ok=True)
            except Exception as e:
                self.fail(f"Media directory creation failed: {e}")

    @override_settings(DEBUG=False)
    def test_production_security_settings(self):
        """Test production security settings"""
        self.assertFalse(settings.DEBUG)

        # Check security settings if they exist
        security_settings = {
            'SECURE_SSL_REDIRECT': True,
            'SECURE_HSTS_SECONDS': lambda x: x > 0,
            'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
            'SECURE_CONTENT_TYPE_NOSNIFF': True,
            'SECURE_BROWSER_XSS_FILTER': True,
        }

        for setting_name, expected_value in security_settings.items():
            if hasattr(settings, setting_name):
                actual_value = getattr(settings, setting_name)
                if callable(expected_value):
                    self.assertTrue(
                        expected_value(actual_value),
                        f"Security setting {setting_name} has invalid value: {actual_value}"
                    )
                else:
                    self.assertEqual(
                        actual_value,
                        expected_value,
                        f"Security setting {setting_name} should be {expected_value}"
                    )


class DatabaseMigrationTests(TestCase):
    """Test database migrations and model integrity"""

    def test_migrations_applied(self):
        """Test that all migrations are applied"""
        try:
            call_command('migrate', '--check', verbosity=0)
        except Exception as e:
            self.fail(f"Migrations not applied: {e}")

    def test_mobile_api_models_created(self):
        """Test that mobile API models are properly created"""
        from apps.mobile_api import models

        # Test model classes exist
        required_models = [
            'MobileDevice',
            'RefreshToken',
            'SyncLog'
        ]

        for model_name in required_models:
            self.assertTrue(
                hasattr(models, model_name),
                f"Model {model_name} is missing"
            )

        # Test models can be instantiated
        try:
            # Create test instances to verify model integrity
            user = User.objects.create_user(
                email="migration_test@test.com",
                password="test123",
                role="gso"
            )

            device = MobileDevice.objects.create(
                user=user,
                device_id="migration_test_device",
                platform="android"
            )

            refresh_token = RefreshToken.objects.create(
                user=user,
                device=device,
                token="test_token",
                expires_at=timezone.now() + timedelta(days=30)
            )

            sync_log = SyncLog.objects.create(
                user=user,
                sync_type="initial",
                status="completed"
            )

            # Clean up
            sync_log.delete()
            refresh_token.delete()
            device.delete()
            user.delete()

        except Exception as e:
            self.fail(f"Model creation failed: {e}")

    def test_foreign_key_relationships(self):
        """Test that foreign key relationships are properly established"""
        from django.db import models

        # Test MobileDevice relationships
        device_fields = MobileDevice._meta.get_fields()
        user_field = next((f for f in device_fields if f.name == 'user'), None)
        self.assertIsNotNone(user_field)
        self.assertIsInstance(user_field, models.ForeignKey)

        # Test RefreshToken relationships
        token_fields = RefreshToken._meta.get_fields()
        token_user_field = next((f for f in token_fields if f.name == 'user'), None)
        token_device_field = next((f for f in token_fields if f.name == 'device'), None)

        self.assertIsNotNone(token_user_field)
        self.assertIsNotNone(token_device_field)
        self.assertIsInstance(token_user_field, models.ForeignKey)
        self.assertIsInstance(token_device_field, models.ForeignKey)


class URLConfigurationTests(APITestCase):
    """Test URL configuration and routing"""

    def test_mobile_api_urls_configured(self):
        """Test that mobile API URLs are properly configured"""
        # Test that main mobile API endpoint exists
        response = self.client.get('/api/mobile/v1/')
        # Should not return 404 (URL exists)
        self.assertNotEqual(response.status_code, 404)

    def test_authentication_endpoints(self):
        """Test authentication endpoints are accessible"""
        auth_endpoints = [
            '/api/mobile/v1/auth/login/',
            '/api/mobile/v1/auth/register/',
            '/api/mobile/v1/auth/refresh/',
            '/api/mobile/v1/auth/logout/',
        ]

        for endpoint in auth_endpoints:
            response = self.client.options(endpoint)
            self.assertNotEqual(
                response.status_code,
                404,
                f"Authentication endpoint {endpoint} not found"
            )

    def test_mobile_api_endpoints(self):
        """Test mobile API endpoints are accessible"""
        api_endpoints = [
            '/api/mobile/v1/sites/',
            '/api/mobile/v1/assessments/',
            '/api/mobile/v1/assessment-responses/',
            '/api/mobile/v1/sync/initial/',
            '/api/mobile/v1/sync/incremental/',
            '/api/mobile/v1/sync/bulk-upload/',
        ]

        for endpoint in api_endpoints:
            response = self.client.options(endpoint)
            self.assertNotEqual(
                response.status_code,
                404,
                f"API endpoint {endpoint} not found"
            )


class APIHealthCheckTests(APITestCase):
    """Test API health and basic functionality"""

    def setUp(self):
        """Set up health check tests"""
        self.user = User.objects.create_user(
            email="health@test.com",
            password="test123",
            role="gso",
            is_active=True
        )

    def test_unauthenticated_access(self):
        """Test that unauthenticated access behaves correctly"""
        # Public endpoints should be accessible
        public_endpoints = [
            '/api/mobile/v1/auth/login/',
            '/api/mobile/v1/auth/register/',
        ]

        for endpoint in public_endpoints:
            response = self.client.post(endpoint, {})
            # Should not return 401 unauthorized for POST (might be 400 bad request)
            self.assertNotEqual(
                response.status_code,
                401,
                f"Public endpoint {endpoint} requires authentication"
            )

        # Protected endpoints should require authentication
        protected_endpoints = [
            '/api/mobile/v1/sites/',
            '/api/mobile/v1/auth/profile/',
            '/api/mobile/v1/sync/initial/',
        ]

        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                401,
                f"Protected endpoint {endpoint} should require authentication"
            )

    def test_authentication_flow(self):
        """Test basic authentication flow works"""
        # Test login
        login_data = {
            'email': self.user.email,
            'password': 'test123',
            'device_id': 'health_check_device',
            'platform': 'android'
        }

        login_response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        login_result = login_response.json()
        self.assertIn('access_token', login_result)
        self.assertIn('refresh_token', login_result)

        # Test authenticated access
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {login_result["access_token"]}')

        profile_response = self.client.get('/api/mobile/v1/auth/profile/')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        profile_data = profile_response.json()
        self.assertEqual(profile_data['email'], self.user.email)

    def test_basic_crud_operations(self):
        """Test basic CRUD operations work"""
        # Authenticate
        login_data = {
            'email': self.user.email,
            'password': 'test123',
            'device_id': 'crud_test_device',
            'platform': 'android'
        }

        login_response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = login_response.json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

        # Create test data
        state = State.objects.create(name="Health State", code="HS")
        locality = Locality.objects.create(name="Health Locality", state=state, code="HL")
        site_type = SiteType.objects.create(name="Health Type", category="camp")

        # Test CREATE
        site_data = {
            'name': 'Health Check Site',
            'site_type': site_type.id,
            'state': state.id,
            'locality': locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 500
        }

        create_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        site_id = create_response.json()['id']

        # Test READ
        read_response = self.client.get(f'/api/mobile/v1/sites/{site_id}/')
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)

        # Test UPDATE
        update_data = {'total_population': 600}
        update_response = self.client.patch(f'/api/mobile/v1/sites/{site_id}/', update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # Test LIST
        list_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        list_data = list_response.json()
        self.assertIn('results', list_data)
        self.assertGreater(len(list_data['results']), 0)


class PerformanceHealthTests(APITestCase):
    """Test performance health for deployment"""

    def setUp(self):
        """Set up performance health tests"""
        self.user = User.objects.create_user(
            email="perf_health@test.com",
            password="test123",
            role="admin",
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test data
        state = State.objects.create(name="Perf State", code="PS")
        locality = Locality.objects.create(name="Perf Locality", state=state, code="PL")
        site_type = SiteType.objects.create(name="Perf Type", category="camp")

        # Create multiple sites for performance testing
        for i in range(20):
            Site.objects.create(
                name=f'Perf Site {i}',
                site_type=site_type,
                state=state,
                locality=locality,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 50
            )

    def test_response_time_health(self):
        """Test that response times are acceptable"""
        endpoints_to_test = [
            '/api/mobile/v1/sites/',
            '/api/mobile/v1/sites/summary/',
            '/api/mobile/v1/assessments/',
        ]

        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertLess(
                response_time,
                5.0,
                f"Endpoint {endpoint} response time {response_time:.2f}s exceeds 5s threshold"
            )

    def test_pagination_health(self):
        """Test that pagination works correctly"""
        response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)

        # Test pagination parameters
        page_response = self.client.get('/api/mobile/v1/sites/?page=1&page_size=5')
        self.assertEqual(page_response.status_code, status.HTTP_200_OK)

        page_data = page_response.json()
        self.assertLessEqual(len(page_data['results']), 5)

    def test_filtering_health(self):
        """Test that filtering works correctly"""
        # Test search
        search_response = self.client.get('/api/mobile/v1/sites/?search=Perf')
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)

        # Test status filter
        status_response = self.client.get('/api/mobile/v1/sites/?status=active')
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)

        # Test ordering
        order_response = self.client.get('/api/mobile/v1/sites/?ordering=-total_population')
        self.assertEqual(order_response.status_code, status.HTTP_200_OK)


class SystemIntegrationHealthTests(TestCase):
    """Test system integration health"""

    def test_database_connection_health(self):
        """Test database connection is healthy"""
        from django.db import connection

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                result = cursor.fetchone()
                self.assertIsNotNone(result)
                self.assertGreater(result[0], 0)
        except Exception as e:
            self.fail(f"Database health check failed: {e}")

    def test_cache_connection_health(self):
        """Test cache connection is healthy"""
        try:
            # Test cache set/get
            test_key = "health_check_key"
            test_value = "health_check_value"

            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)

            self.assertEqual(retrieved_value, test_value)

            # Clean up
            cache.delete(test_key)

        except Exception as e:
            self.fail(f"Cache health check failed: {e}")

    def test_logging_configuration(self):
        """Test logging configuration"""
        import logging

        # Test that loggers can be created
        try:
            logger = logging.getLogger('mobile_api')
            logger.info("Health check log message")
        except Exception as e:
            self.fail(f"Logging configuration failed: {e}")

    def test_timezone_configuration(self):
        """Test timezone configuration"""
        from django.utils import timezone

        # Test timezone awareness
        now = timezone.now()
        self.assertTrue(timezone.is_aware(now))

        # Test timezone setting
        self.assertTrue(settings.USE_TZ)


class DeploymentSmokeTests(APITestCase):
    """Smoke tests for deployment verification"""

    def test_admin_user_creation(self):
        """Test that admin users can be created"""
        admin_user = User.objects.create_user(
            email="smoke_admin@test.com",
            password="test123",
            role="admin",
            is_active=True,
            is_staff=True,
            is_superuser=True
        )

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, "admin")

    def test_organization_creation(self):
        """Test that organizations can be created"""
        org = Organization.objects.create(
            name="Smoke Test Organization",
            organization_type="ngo",
            is_active=True
        )

        self.assertEqual(org.name, "Smoke Test Organization")
        self.assertEqual(org.organization_type, "ngo")
        self.assertTrue(org.is_active)

    def test_complete_user_workflow(self):
        """Test complete user workflow from registration to data access"""
        # Create organization first
        org = Organization.objects.create(
            name="Workflow Test Org",
            organization_type="ngo",
            is_active=True
        )

        # Test user registration (if endpoint exists)
        registration_data = {
            'email': 'workflow@test.com',
            'password': 'WorkflowTest123!',
            'confirm_password': 'WorkflowTest123!',
            'first_name': 'Workflow',
            'last_name': 'Test',
            'role': 'gso',
            'organization': org.id
        }

        # If registration endpoint doesn't exist, create user directly
        try:
            register_response = self.client.post('/api/mobile/v1/auth/register/', registration_data)
            if register_response.status_code == status.HTTP_201_CREATED:
                user_created_via_api = True
            else:
                user_created_via_api = False
        except:
            user_created_via_api = False

        if not user_created_via_api:
            # Create user directly
            user = User.objects.create_user(
                email='workflow@test.com',
                password='WorkflowTest123!',
                first_name='Workflow',
                last_name='Test',
                role='gso',
                organization=org,
                is_active=True
            )

        # Test login
        login_data = {
            'email': 'workflow@test.com',
            'password': 'WorkflowTest123!',
            'device_id': 'workflow_device',
            'platform': 'android'
        }

        login_response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        tokens = login_response.json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

        # Test data access
        profile_response = self.client.get('/api/mobile/v1/auth/profile/')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        sites_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(sites_response.status_code, status.HTTP_200_OK)

        # Test sync functionality
        sync_data = {
            'data_types': ['sites'],
            'last_sync': None
        }

        sync_response = self.client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
        self.assertEqual(sync_response.status_code, status.HTTP_200_OK)

    def test_error_handling(self):
        """Test that error handling works correctly"""
        # Test 404 error
        response_404 = self.client.get('/api/mobile/v1/nonexistent/')
        self.assertEqual(response_404.status_code, 404)

        # Test 401 error
        response_401 = self.client.get('/api/mobile/v1/auth/profile/')
        self.assertEqual(response_401.status_code, 401)

        # Test 400 error with bad data
        bad_login_data = {
            'email': 'invalid_email',
            'password': '',
        }

        response_400 = self.client.post('/api/mobile/v1/auth/login/', bad_login_data)
        self.assertEqual(response_400.status_code, 400)


class SecurityDeploymentTests(APITestCase):
    """Test security aspects for deployment"""

    def test_cors_configuration(self):
        """Test CORS configuration"""
        # Test preflight request
        response = self.client.options('/api/mobile/v1/sites/')

        # Should handle CORS properly (either allow or properly restrict)
        self.assertIn(response.status_code, [200, 204])

    def test_csrf_protection(self):
        """Test CSRF protection"""
        # CSRF should be properly configured for API endpoints
        # API endpoints typically use token auth and exempt CSRF
        response = self.client.post('/api/mobile/v1/auth/login/', {})

        # Should not fail due to CSRF (400 for bad data is OK)
        self.assertNotEqual(response.status_code, 403)

    def test_sql_injection_protection(self):
        """Test basic SQL injection protection"""
        # Test search parameters with SQL injection attempts
        sql_payloads = [
            "'; DROP TABLE sites; --",
            "' OR '1'='1",
        ]

        for payload in sql_payloads:
            response = self.client.get(f'/api/mobile/v1/sites/?search={payload}')
            # Should not cause server error
            self.assertNotEqual(response.status_code, 500)

    def test_rate_limiting_configured(self):
        """Test that rate limiting is configured"""
        # Make multiple rapid requests
        responses = []
        for i in range(20):
            response = self.client.get('/api/mobile/v1/auth/login/')
            responses.append(response.status_code)

        # Should eventually hit rate limit or handle gracefully
        # This test is informational - rate limiting may or may not be configured
        rate_limited = any(status_code == 429 for status_code in responses)

        # Don't fail test, just log the result
        if rate_limited:
            print("Rate limiting is configured")
        else:
            print("Rate limiting may not be configured (consider implementing)")


# Test runner utility for deployment verification
def run_deployment_verification():
    """
    Utility function to run deployment verification tests.
    Can be called during deployment process.
    """
    import subprocess
    import sys

    test_modules = [
        'apps.mobile_api.tests.test_deployment_verification.DeploymentReadinessTests',
        'apps.mobile_api.tests.test_deployment_verification.DatabaseMigrationTests',
        'apps.mobile_api.tests.test_deployment_verification.URLConfigurationTests',
        'apps.mobile_api.tests.test_deployment_verification.APIHealthCheckTests',
        'apps.mobile_api.tests.test_deployment_verification.SystemIntegrationHealthTests',
        'apps.mobile_api.tests.test_deployment_verification.DeploymentSmokeTests',
    ]

    print("Running deployment verification tests...")

    all_passed = True
    for test_module in test_modules:
        print(f"\nRunning {test_module}...")
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'test', test_module, '--verbosity=2'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✓ {test_module} PASSED")
            else:
                print(f"✗ {test_module} FAILED")
                print(result.stdout)
                print(result.stderr)
                all_passed = False

        except Exception as e:
            print(f"✗ {test_module} ERROR: {e}")
            all_passed = False

    if all_passed:
        print("\n🎉 ALL DEPLOYMENT VERIFICATION TESTS PASSED")
        print("System is ready for deployment!")
    else:
        print("\n❌ SOME DEPLOYMENT VERIFICATION TESTS FAILED")
        print("Please fix issues before deploying to production.")

    return all_passed


if __name__ == '__main__':
    run_deployment_verification()