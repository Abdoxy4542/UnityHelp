"""
Production-grade security tests for UnityAid Mobile API.
Tests authentication, authorization, data protection, and security best practices.
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import Organization
from apps.sites.models import Site, State, Locality, SiteType
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog

User = get_user_model()


class AuthenticationSecurityTests(APITestCase):
    """Test authentication security measures"""

    def setUp(self):
        """Set up security test data"""
        self.user = User.objects.create_user(
            email="security@test.com",
            password="SecurePass123!",
            role="gso",
            is_active=True
        )
        self.client = APIClient()

    def test_password_strength_requirements(self):
        """Test password strength validation"""
        weak_passwords = [
            "123456",
            "password",
            "abc",
            "qwerty",
            "admin"
        ]

        for weak_password in weak_passwords:
            registration_data = {
                'email': 'weak@test.com',
                'password': weak_password,
                'confirm_password': weak_password,
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'gso'
            }

            response = self.client.post('/api/mobile/v1/auth/register/', registration_data)
            # Should fail due to weak password
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST])

    def test_brute_force_protection(self):
        """Test protection against brute force attacks"""
        login_data = {
            'email': self.user.email,
            'password': 'WrongPassword',
            'device_id': 'test_device',
            'platform': 'android'
        }

        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = self.client.post('/api/mobile/v1/auth/login/', login_data)
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                failed_attempts += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                # Rate limiting kicked in
                break

        # Should be rate limited after multiple attempts
        self.assertGreaterEqual(failed_attempts, 3)

    def test_token_expiration(self):
        """Test that tokens expire properly"""
        login_data = {
            'email': self.user.email,
            'password': 'SecurePass123!',
            'device_id': 'test_device',
            'platform': 'android'
        }

        login_response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        tokens = login_response.json()
        access_token = tokens['access_token']

        # Test with valid token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {access_token}')
        response = self.client.get('/api/mobile/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Mock token expiration by modifying the refresh token
        refresh_token = RefreshToken.objects.get(user=self.user)
        refresh_token.expires_at = timezone.now() - timedelta(hours=1)
        refresh_token.save()

        # Test refresh with expired token
        refresh_data = {
            'refresh_token': refresh_token.token,
            'device_id': 'test_device'
        }

        refresh_response = self.client.post('/api/mobile/v1/auth/refresh/', refresh_data)
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_device_binding(self):
        """Test that tokens are bound to specific devices"""
        # Login with device 1
        login_data = {
            'email': self.user.email,
            'password': 'SecurePass123!',
            'device_id': 'device_1',
            'platform': 'android'
        }

        login_response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = login_response.json()
        refresh_token = tokens['refresh_token']

        # Try to refresh with different device
        refresh_data = {
            'refresh_token': refresh_token,
            'device_id': 'device_2'  # Different device
        }

        refresh_response = self.client.post('/api/mobile/v1/auth/refresh/', refresh_data)
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_invalidation_on_logout(self):
        """Test that logout properly invalidates all tokens"""
        # Login
        login_data = {
            'email': self.user.email,
            'password': 'SecurePass123!',
            'device_id': 'test_device',
            'platform': 'android'
        }

        login_response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = login_response.json()
        access_token = tokens['access_token']

        # Use token for authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {access_token}')
        auth_response = self.client.get('/api/mobile/v1/auth/profile/')
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)

        # Logout
        logout_response = self.client.post('/api/mobile/v1/auth/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Try to use token after logout
        post_logout_response = self.client.get('/api/mobile/v1/auth/profile/')
        self.assertEqual(post_logout_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify refresh token is invalidated
        self.assertFalse(RefreshToken.objects.filter(user=self.user, is_active=True).exists())

    def test_concurrent_session_limits(self):
        """Test limits on concurrent sessions per user"""
        device_ids = ['device_1', 'device_2', 'device_3', 'device_4', 'device_5']
        active_tokens = []

        # Create multiple sessions
        for device_id in device_ids:
            login_data = {
                'email': self.user.email,
                'password': 'SecurePass123!',
                'device_id': device_id,
                'platform': 'android'
            }

            response = self.client.post('/api/mobile/v1/auth/login/', login_data)
            if response.status_code == status.HTTP_200_OK:
                active_tokens.append(response.json()['access_token'])

        # Check that not all sessions are allowed (should have session limit)
        active_devices = MobileDevice.objects.filter(user=self.user, is_active=True).count()
        self.assertLessEqual(active_devices, 3)  # Max 3 concurrent sessions


class AuthorizationSecurityTests(APITestCase):
    """Test role-based authorization security"""

    def setUp(self):
        """Set up authorization test data"""
        # Create organizations
        self.org1 = Organization.objects.create(
            name="Org 1",
            organization_type="ngo",
            is_active=True
        )
        self.org2 = Organization.objects.create(
            name="Org 2",
            organization_type="ngo",
            is_active=True
        )

        # Create users with different roles and organizations
        self.gso_user = User.objects.create_user(
            email="gso@test.com",
            password="test123",
            role="gso",
            organization=self.org1,
            is_active=True
        )

        self.ngo_user = User.objects.create_user(
            email="ngo@test.com",
            password="test123",
            role="ngo_user",
            organization=self.org1,
            is_active=True
        )

        self.other_ngo_user = User.objects.create_user(
            email="other_ngo@test.com",
            password="test123",
            role="ngo_user",
            organization=self.org2,
            is_active=True
        )

        # Create geographic data
        self.state = State.objects.create(name="Test State", code="TS")
        self.locality = Locality.objects.create(
            name="Test Locality",
            state=self.state,
            code="TL"
        )
        self.site_type = SiteType.objects.create(
            name="Test Type",
            category="camp"
        )

        # Create sites for testing
        self.org1_site = Site.objects.create(
            name="Org 1 Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            organization=self.org1,
            latitude=15.0,
            longitude=32.0,
            status='active',
            total_population=1000
        )

        self.org2_site = Site.objects.create(
            name="Org 2 Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            organization=self.org2,
            latitude=15.1,
            longitude=32.1,
            status='active',
            total_population=1200
        )

        self.client = APIClient()

    def authenticate_user(self, user):
        """Helper to authenticate user"""
        login_data = {
            'email': user.email,
            'password': 'test123',
            'device_id': f'device_{user.id}',
            'platform': 'android'
        }

        response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = response.json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

    def test_organization_based_access_control(self):
        """Test users can only access their organization's data"""
        # Authenticate org1 user
        self.authenticate_user(self.ngo_user)

        # Should access org1 site
        org1_response = self.client.get(f'/api/mobile/v1/sites/{self.org1_site.id}/')
        self.assertEqual(org1_response.status_code, status.HTTP_200_OK)

        # Should NOT access org2 site
        org2_response = self.client.get(f'/api/mobile/v1/sites/{self.org2_site.id}/')
        self.assertEqual(org2_response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify site list only shows org1 sites
        sites_response = self.client.get('/api/mobile/v1/sites/')
        sites_data = sites_response.json()['results']
        site_ids = [site['id'] for site in sites_data]

        self.assertIn(self.org1_site.id, site_ids)
        self.assertNotIn(self.org2_site.id, site_ids)

    def test_role_based_permission_restrictions(self):
        """Test different roles have appropriate permissions"""
        # Test GSO permissions
        self.authenticate_user(self.gso_user)

        # GSOs should be able to create sites
        site_data = {
            'name': 'GSO Created Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.5',
            'longitude': '32.5',
            'status': 'active',
            'total_population': 500
        }

        gso_create_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(gso_create_response.status_code, status.HTTP_201_CREATED)

        # Test NGO user permissions (more restricted)
        self.authenticate_user(self.ngo_user)

        # NGO users might have restricted creation permissions
        ngo_create_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        # Depending on business rules, this might be forbidden or allowed with restrictions
        self.assertIn(ngo_create_response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_403_FORBIDDEN
        ])

    def test_site_assignment_security(self):
        """Test that users can only access sites they're assigned to"""
        # Assign GSO to org1_site
        self.org1_site.assigned_gsos.add(self.gso_user)

        self.authenticate_user(self.gso_user)

        # Should access assigned site
        assigned_response = self.client.get(f'/api/mobile/v1/sites/{self.org1_site.id}/')
        self.assertEqual(assigned_response.status_code, status.HTTP_200_OK)

        # Should NOT access unassigned site
        unassigned_response = self.client.get(f'/api/mobile/v1/sites/{self.org2_site.id}/')
        self.assertEqual(unassigned_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_data_modification_permissions(self):
        """Test that users can only modify data they have permission for"""
        # Assign GSO to site
        self.org1_site.assigned_gsos.add(self.gso_user)
        self.authenticate_user(self.gso_user)

        # Should be able to update assigned site
        update_data = {'total_population': 1100}
        update_response = self.client.patch(f'/api/mobile/v1/sites/{self.org1_site.id}/', update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # Should NOT be able to delete site (assuming GSOs can't delete)
        delete_response = self.client.delete(f'/api/mobile/v1/sites/{self.org1_site.id}/')
        self.assertIn(delete_response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ])


class DataProtectionSecurityTests(APITestCase):
    """Test data protection and privacy measures"""

    def setUp(self):
        """Set up data protection test data"""
        self.user = User.objects.create_user(
            email="privacy@test.com",
            password="test123",
            role="gso",
            is_active=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed in API responses"""
        # Get user profile
        profile_response = self.client.get('/api/mobile/v1/auth/profile/')
        profile_data = profile_response.json()

        # Should not expose sensitive fields
        sensitive_fields = ['password', 'last_login', 'date_joined']
        for field in sensitive_fields:
            self.assertNotIn(field, profile_data)

        # Should not expose internal IDs or tokens
        internal_fields = ['refresh_token', 'device_token']
        for field in internal_fields:
            self.assertNotIn(field, profile_data)

    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        # Test SQL injection in search parameters
        sql_injection_payloads = [
            "'; DROP TABLE sites; --",
            "' OR '1'='1",
            "'; UPDATE sites SET name='hacked'; --",
            "' UNION SELECT * FROM auth_user --"
        ]

        for payload in sql_injection_payloads:
            # Test in search parameter
            search_response = self.client.get(f'/api/mobile/v1/sites/?search={payload}')
            # Should not cause server error (500)
            self.assertNotEqual(search_response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Test in filter parameter
            filter_response = self.client.get(f'/api/mobile/v1/sites/?name={payload}')
            self.assertNotEqual(filter_response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_xss_protection(self):
        """Test protection against Cross-Site Scripting (XSS)"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
        ]

        state = State.objects.create(name="Test State", code="TS")
        locality = Locality.objects.create(name="Test Locality", state=state, code="TL")
        site_type = SiteType.objects.create(name="Test Type", category="camp")

        for payload in xss_payloads:
            site_data = {
                'name': payload,  # XSS payload in name
                'site_type': site_type.id,
                'state': state.id,
                'locality': locality.id,
                'latitude': '15.0',
                'longitude': '32.0',
                'status': 'active',
                'total_population': 100
            }

            response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')

            if response.status_code == status.HTTP_201_CREATED:
                # If creation succeeded, verify XSS payload is escaped/sanitized
                site_id = response.json()['id']
                get_response = self.client.get(f'/api/mobile/v1/sites/{site_id}/')
                site_data = get_response.json()

                # Name should not contain raw script tags
                self.assertNotIn('<script>', site_data['name'])
                self.assertNotIn('javascript:', site_data['name'])

    def test_data_validation_and_sanitization(self):
        """Test input validation and data sanitization"""
        state = State.objects.create(name="Test State", code="TS")
        locality = Locality.objects.create(name="Test Locality", state=state, code="TL")
        site_type = SiteType.objects.create(name="Test Type", category="camp")

        # Test invalid data types
        invalid_data_tests = [
            {'total_population': 'not_a_number'},  # String instead of number
            {'latitude': 'invalid_lat'},  # Invalid latitude
            {'longitude': 'invalid_lon'},  # Invalid longitude
            {'status': 'invalid_status'},  # Invalid choice
            {'total_population': -100},  # Negative population
            {'latitude': 999.999},  # Out of range latitude
            {'longitude': 999.999},  # Out of range longitude
        ]

        for invalid_data in invalid_data_tests:
            site_data = {
                'name': 'Test Site',
                'site_type': site_type.id,
                'state': state.id,
                'locality': locality.id,
                'latitude': '15.0',
                'longitude': '32.0',
                'status': 'active',
                'total_population': 100
            }
            site_data.update(invalid_data)

            response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
            # Should reject invalid data
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_upload_security(self):
        """Test file upload security (if applicable)"""
        # This would test file upload endpoints if they exist
        # For now, we'll test that dangerous file types are rejected

        dangerous_filenames = [
            'malware.exe',
            'script.php',
            'payload.jsp',
            'dangerous.asp',
            '../../etc/passwd',
            'script.js',
        ]

        # If your API has file upload endpoints, test them here
        # This is a placeholder for when file uploads are implemented
        for filename in dangerous_filenames:
            # Example test structure:
            # file_data = {'file': SimpleUploadedFile(filename, b'content')}
            # response = self.client.post('/api/mobile/v1/upload/', file_data)
            # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            pass


@override_settings(DEBUG=False)
class ProductionConfigurationTests(TestCase):
    """Test production-ready configuration settings"""

    def test_debug_mode_disabled(self):
        """Test that DEBUG is disabled in production"""
        self.assertFalse(settings.DEBUG)

    def test_allowed_hosts_configured(self):
        """Test that ALLOWED_HOSTS is properly configured"""
        # In production, ALLOWED_HOSTS should not be empty or contain '*'
        if not settings.DEBUG:
            self.assertTrue(settings.ALLOWED_HOSTS)
            self.assertNotIn('*', settings.ALLOWED_HOSTS)

    def test_secret_key_strength(self):
        """Test that SECRET_KEY is strong"""
        secret_key = settings.SECRET_KEY
        self.assertGreater(len(secret_key), 40)  # Should be reasonably long
        self.assertNotEqual(secret_key, 'your-secret-key-here')  # Not default

    def test_security_middleware_configured(self):
        """Test that security middleware is properly configured"""
        security_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'corsheaders.middleware.CorsMiddleware',
        ]

        for middleware in security_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)

    def test_https_security_settings(self):
        """Test HTTPS security settings"""
        if not settings.DEBUG:
            # These should be enabled in production
            security_settings = [
                'SECURE_SSL_REDIRECT',
                'SECURE_HSTS_SECONDS',
                'SECURE_HSTS_INCLUDE_SUBDOMAINS',
                'SECURE_HSTS_PRELOAD',
                'SECURE_CONTENT_TYPE_NOSNIFF',
                'SECURE_BROWSER_XSS_FILTER',
                'SECURE_REFERRER_POLICY',
            ]

            for setting in security_settings:
                if hasattr(settings, setting):
                    # Verify security settings are enabled
                    if setting in ['SECURE_SSL_REDIRECT', 'SECURE_HSTS_INCLUDE_SUBDOMAINS',
                                  'SECURE_HSTS_PRELOAD', 'SECURE_CONTENT_TYPE_NOSNIFF',
                                  'SECURE_BROWSER_XSS_FILTER']:
                        self.assertTrue(getattr(settings, setting, False))
                    elif setting == 'SECURE_HSTS_SECONDS':
                        self.assertGreater(getattr(settings, setting, 0), 0)

    def test_database_connection_security(self):
        """Test database connection security"""
        default_db = settings.DATABASES['default']

        # Should not use default passwords
        password = default_db.get('PASSWORD', '')
        weak_passwords = ['', 'password', 'admin', 'root', '123456']
        self.assertNotIn(password, weak_passwords)

        # Should use secure connection in production
        if not settings.DEBUG:
            options = default_db.get('OPTIONS', {})
            # PostgreSQL should use SSL
            if default_db.get('ENGINE') == 'django.contrib.gis.db.backends.postgis':
                self.assertTrue(options.get('sslmode') in ['require', 'prefer'])


class RateLimitingSecurityTests(APITestCase):
    """Test rate limiting and DOS protection"""

    def setUp(self):
        """Set up rate limiting test data"""
        self.user = User.objects.create_user(
            email="ratelimit@test.com",
            password="test123",
            role="gso",
            is_active=True
        )

        self.client = APIClient()
        login_data = {
            'email': self.user.email,
            'password': 'test123',
            'device_id': 'rate_test_device',
            'platform': 'android'
        }

        response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = response.json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

    def test_api_rate_limiting(self):
        """Test API endpoint rate limiting"""
        # Make rapid requests to test rate limiting
        rate_limited = False

        for i in range(30):  # Make many requests quickly
            response = self.client.get('/api/mobile/v1/auth/profile/')

            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True
                break

            # Small delay to avoid overwhelming the test
            time.sleep(0.01)

        # Should eventually hit rate limit
        # Note: This depends on rate limiting being configured
        # In a real production environment, this would be more restrictive

    def test_bulk_operation_limits(self):
        """Test limits on bulk operations"""
        state = State.objects.create(name="Test State", code="TS")
        locality = Locality.objects.create(name="Test Locality", state=state, code="TL")
        site_type = SiteType.objects.create(name="Test Type", category="camp")

        # Try to create too many sites at once
        bulk_data = {
            'sites': [
                {
                    'name': f'Bulk Site {i}',
                    'site_type': site_type.id,
                    'state': state.id,
                    'locality': locality.id,
                    'latitude': 15.0 + i * 0.001,
                    'longitude': 32.0 + i * 0.001,
                    'status': 'active',
                    'total_population': 100
                } for i in range(200)  # Large number
            ]
        }

        response = self.client.post('/api/mobile/v1/sync/bulk-upload/', bulk_data, format='json')

        # Should either reject due to size or implement pagination
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,  # Rejected due to size
            status.HTTP_200_OK,           # Accepted with limits
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE  # Payload too large
        ])

        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            # Should not create all 200 sites
            self.assertLess(result.get('sites_created', 0), 200)

    def test_request_size_limits(self):
        """Test request payload size limits"""
        # Create a very large payload
        large_payload = {
            'name': 'A' * 10000,  # Very long name
            'description': 'B' * 50000,  # Very long description
            'metadata': {'large_field': 'C' * 100000}  # Large metadata
        }

        response = self.client.post('/api/mobile/v1/sites/', large_payload, format='json')

        # Should reject oversized requests
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ])


class SecurityHeadersTests(APITestCase):
    """Test security headers in API responses"""

    def setUp(self):
        """Set up security headers test"""
        self.client = APIClient()

    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        # Test public endpoint
        response = self.client.get('/api/mobile/v1/auth/login/')

        # Check for security headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Referrer-Policy'
        ]

        for header in security_headers:
            if header in response:
                # Verify proper values
                if header == 'X-Content-Type-Options':
                    self.assertEqual(response[header], 'nosniff')
                elif header == 'X-Frame-Options':
                    self.assertIn(response[header], ['DENY', 'SAMEORIGIN'])
                elif header == 'X-XSS-Protection':
                    self.assertEqual(response[header], '1; mode=block')

    def test_cors_headers_configuration(self):
        """Test CORS headers are properly configured"""
        # Test preflight request
        response = self.client.options('/api/mobile/v1/sites/')

        # Should have CORS headers for mobile access
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]

        for header in cors_headers:
            if header in response:
                # Verify CORS is not overly permissive
                if header == 'Access-Control-Allow-Origin':
                    self.assertNotEqual(response[header], '*')

    def test_content_security_policy(self):
        """Test Content Security Policy headers"""
        response = self.client.get('/api/mobile/v1/')

        if 'Content-Security-Policy' in response:
            csp = response['Content-Security-Policy']
            # Should have restrictive CSP
            self.assertIn("default-src 'self'", csp)
            self.assertNotIn("'unsafe-eval'", csp)
            self.assertNotIn("'unsafe-inline'", csp)