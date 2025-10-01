"""
Production-grade performance tests for UnityAid Mobile API.
Tests load handling, response times, database optimization, and scalability.
"""

import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import Organization
from apps.sites.models import Site, State, Locality, SiteType, Facility
from apps.assessments.models import Assessment, AssessmentResponse
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog

User = get_user_model()


class ResponseTimePerformanceTests(APITestCase):
    """Test API response times meet production requirements"""

    def setUp(self):
        """Set up performance test data"""
        # Create test user
        self.user = User.objects.create_user(
            email="perf@test.com",
            password="test123",
            role="gso",
            is_active=True
        )

        # Create basic geographic data
        self.state = State.objects.create(name="Performance State", code="PS")
        self.locality = Locality.objects.create(
            name="Performance Locality",
            state=self.state,
            code="PL"
        )
        self.site_type = SiteType.objects.create(
            name="Performance Type",
            category="camp"
        )

        # Authenticate user
        self.client = APIClient()
        login_data = {
            'email': self.user.email,
            'password': 'test123',
            'device_id': 'perf_device',
            'platform': 'android'
        }

        response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = response.json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

        # Create test sites for performance testing
        self.create_test_sites(50)

    def create_test_sites(self, count):
        """Create test sites for performance testing"""
        sites = []
        for i in range(count):
            site = Site.objects.create(
                name=f'Performance Site {i}',
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 50
            )
            site.assigned_gsos.add(self.user)
            sites.append(site)

            # Add facilities to some sites
            if i % 3 == 0:
                Facility.objects.create(
                    site=site,
                    name=f'Facility {i}',
                    facility_type='health',
                    capacity=100,
                    current_usage=80,
                    is_functional=True
                )

        return sites

    def measure_response_time(self, method, url, data=None):
        """Helper to measure API response time"""
        start_time = time.time()

        if method.upper() == 'GET':
            response = self.client.get(url)
        elif method.upper() == 'POST':
            response = self.client.post(url, data or {}, format='json')
        elif method.upper() == 'PATCH':
            response = self.client.patch(url, data or {}, format='json')

        end_time = time.time()
        response_time = end_time - start_time

        return response, response_time

    def test_list_endpoints_response_time(self):
        """Test that list endpoints respond within acceptable time"""
        endpoints = [
            '/api/mobile/v1/sites/',
            '/api/mobile/v1/assessments/',
            '/api/mobile/v1/assessment-responses/',
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response, response_time = self.measure_response_time('GET', endpoint)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertLess(response_time, 2.0, f'{endpoint} took {response_time:.2f}s')

                # Log performance metrics
                print(f'{endpoint}: {response_time:.3f}s')

    def test_detail_endpoints_response_time(self):
        """Test that detail endpoints respond quickly"""
        site = Site.objects.filter(assigned_gsos=self.user).first()

        endpoints = [
            f'/api/mobile/v1/sites/{site.id}/',
            '/api/mobile/v1/auth/profile/',
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response, response_time = self.measure_response_time('GET', endpoint)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertLess(response_time, 1.0, f'{endpoint} took {response_time:.2f}s')

    def test_create_operations_response_time(self):
        """Test that create operations are performant"""
        site_data = {
            'name': 'Performance Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.999',
            'longitude': '32.999',
            'status': 'active',
            'total_population': 500
        }

        response, response_time = self.measure_response_time(
            'POST', '/api/mobile/v1/sites/', site_data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertLess(response_time, 3.0, f'Site creation took {response_time:.2f}s')

    def test_update_operations_response_time(self):
        """Test that update operations are performant"""
        site = Site.objects.filter(assigned_gsos=self.user).first()

        update_data = {
            'total_population': 1500,
            'status': 'active'
        }

        response, response_time = self.measure_response_time(
            'PATCH', f'/api/mobile/v1/sites/{site.id}/', update_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 2.0, f'Site update took {response_time:.2f}s')

    def test_sync_operations_response_time(self):
        """Test that sync operations complete within reasonable time"""
        sync_data = {
            'data_types': ['sites'],
            'last_sync': None
        }

        response, response_time = self.measure_response_time(
            'POST', '/api/mobile/v1/sync/initial/', sync_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 10.0, f'Initial sync took {response_time:.2f}s')

        # Verify response contains expected data
        sync_result = response.json()
        self.assertIn('sites', sync_result)
        self.assertGreater(len(sync_result['sites']), 0)

    def test_search_operations_response_time(self):
        """Test that search operations are performant"""
        search_params = [
            '?search=Performance',
            '?status=active',
            '?total_population__gte=500',
            '?search=Site&status=active'
        ]

        for params in search_params:
            with self.subTest(params=params):
                response, response_time = self.measure_response_time(
                    'GET', f'/api/mobile/v1/sites/{params}'
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertLess(response_time, 3.0, f'Search {params} took {response_time:.2f}s')


class DatabaseOptimizationTests(APITestCase):
    """Test database query optimization"""

    def setUp(self):
        """Set up database optimization tests"""
        self.user = User.objects.create_user(
            email="db_perf@test.com",
            password="test123",
            role="admin",  # Admin to see all data
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test data
        self.state = State.objects.create(name="DB Test State", code="DTS")
        self.locality = Locality.objects.create(
            name="DB Test Locality",
            state=self.state,
            code="DTL"
        )
        self.site_type = SiteType.objects.create(
            name="DB Test Type",
            category="camp"
        )

        # Create sites with relationships
        self.create_complex_test_data()

    def create_complex_test_data(self):
        """Create complex test data with relationships"""
        # Create organization
        self.org = Organization.objects.create(
            name="DB Test Org",
            organization_type="ngo",
            is_active=True
        )

        # Create users
        self.gso_users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f"gso{i}@test.com",
                password="test123",
                role="gso",
                organization=self.org,
                is_active=True
            )
            self.gso_users.append(user)

        # Create sites with complex relationships
        for i in range(20):
            site = Site.objects.create(
                name=f'DB Test Site {i}',
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                organization=self.org,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 50
            )

            # Assign GSOs
            site.assigned_gsos.set(self.gso_users[:3])

            # Create facilities
            for j in range(3):
                Facility.objects.create(
                    site=site,
                    name=f'Facility {i}-{j}',
                    facility_type=['health', 'education', 'water'][j],
                    capacity=50 + j * 25,
                    current_usage=30 + j * 15,
                    is_functional=True
                )

    def count_queries(self, func):
        """Helper to count database queries"""
        initial_queries = len(connection.queries)
        func()
        final_queries = len(connection.queries)
        return final_queries - initial_queries

    def test_sites_list_query_optimization(self):
        """Test that sites list uses optimal number of queries"""
        def get_sites_list():
            response = self.client.get('/api/mobile/v1/sites/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response

        query_count = self.count_queries(get_sites_list)

        # Should use select_related and prefetch_related to minimize queries
        # Expected: 1 for sites + 1 for related objects (optimized)
        self.assertLess(query_count, 10, f'Sites list used {query_count} queries')

    def test_site_detail_query_optimization(self):
        """Test that site detail uses optimal queries"""
        site = Site.objects.first()

        def get_site_detail():
            response = self.client.get(f'/api/mobile/v1/sites/{site.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response

        query_count = self.count_queries(get_site_detail)

        # Should efficiently fetch related data
        self.assertLess(query_count, 5, f'Site detail used {query_count} queries')

    def test_sync_query_optimization(self):
        """Test that sync operations are query-optimized"""
        sync_data = {
            'data_types': ['sites'],
            'last_sync': None
        }

        def perform_sync():
            response = self.client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response

        query_count = self.count_queries(perform_sync)

        # Sync should be efficient even with many sites
        self.assertLess(query_count, 15, f'Sync used {query_count} queries')

    def test_bulk_operations_query_optimization(self):
        """Test that bulk operations are optimized"""
        bulk_data = {
            'sites': [
                {
                    'name': f'Bulk Site {i}',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': 14.0 + i * 0.01,
                    'longitude': 31.0 + i * 0.01,
                    'status': 'active',
                    'total_population': 200 + i * 25
                } for i in range(5)
            ]
        }

        def perform_bulk_upload():
            response = self.client.post('/api/mobile/v1/sync/bulk-upload/', bulk_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response

        query_count = self.count_queries(perform_bulk_upload)

        # Bulk operations should use bulk_create for efficiency
        self.assertLess(query_count, 20, f'Bulk upload used {query_count} queries')


class CachingPerformanceTests(APITestCase):
    """Test caching improves performance"""

    def setUp(self):
        """Set up caching tests"""
        self.user = User.objects.create_user(
            email="cache@test.com",
            password="test123",
            role="gso",
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Clear cache before tests
        cache.clear()

    @patch('apps.mobile_api.v1.views.cache')
    def test_site_summary_caching(self, mock_cache):
        """Test that site summary uses caching effectively"""
        # Configure mock cache for cache miss
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        # First request (cache miss)
        response1 = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Verify cache was called
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()

        # Configure for cache hit
        cached_data = {
            'total_sites': 10,
            'total_population': 5000,
            'active_sites': 8,
            'inactive_sites': 2
        }
        mock_cache.get.return_value = cached_data

        # Second request (cache hit)
        response2 = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify cached data was returned
        self.assertEqual(response2.json(), cached_data)

    def test_cache_invalidation(self):
        """Test that cache is properly invalidated on updates"""
        state = State.objects.create(name="Cache State", code="CS")
        locality = Locality.objects.create(name="Cache Locality", state=state, code="CL")
        site_type = SiteType.objects.create(name="Cache Type", category="camp")

        # Get initial summary (populate cache)
        response1 = self.client.get('/api/mobile/v1/sites/summary/')
        initial_count = response1.json().get('total_sites', 0)

        # Create new site (should invalidate cache)
        site_data = {
            'name': 'Cache Test Site',
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

        # Get summary again (should reflect new site)
        response2 = self.client.get('/api/mobile/v1/sites/summary/')
        new_count = response2.json().get('total_sites', 0)

        # Count should have increased (cache invalidated)
        self.assertGreater(new_count, initial_count)


class ConcurrentAccessTests(TransactionTestCase):
    """Test concurrent access performance and safety"""

    def setUp(self):
        """Set up concurrent access tests"""
        # Create multiple users
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f"concurrent{i}@test.com",
                password="test123",
                role="gso",
                is_active=True
            )
            self.users.append(user)

        # Create basic data
        self.state = State.objects.create(name="Concurrent State", code="CS")
        self.locality = Locality.objects.create(
            name="Concurrent Locality",
            state=self.state,
            code="CL"
        )
        self.site_type = SiteType.objects.create(
            name="Concurrent Type",
            category="camp"
        )

    def authenticate_client(self, user):
        """Helper to create authenticated client for user"""
        client = APIClient()
        login_data = {
            'email': user.email,
            'password': 'test123',
            'device_id': f'device_{user.id}',
            'platform': 'android'
        }

        response = client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = response.json()
        client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')
        return client

    def test_concurrent_site_creation(self):
        """Test concurrent site creation performance"""
        results = []
        errors = []

        def create_site(user_index):
            """Function to create site concurrently"""
            try:
                user = self.users[user_index]
                client = self.authenticate_client(user)

                site_data = {
                    'name': f'Concurrent Site {user_index}',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': 15.0 + user_index * 0.01,
                    'longitude': 32.0 + user_index * 0.01,
                    'status': 'active',
                    'total_population': 100 + user_index * 50
                }

                start_time = time.time()
                response = client.post('/api/mobile/v1/sites/', site_data, format='json')
                end_time = time.time()

                results.append({
                    'user_index': user_index,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == status.HTTP_201_CREATED
                })

            except Exception as e:
                errors.append({
                    'user_index': user_index,
                    'error': str(e)
                })

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_site, i) for i in range(5)]
            for future in futures:
                future.result()  # Wait for completion

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)

        success_count = sum(1 for r in results if r['success'])
        self.assertEqual(success_count, 5, "All concurrent creations should succeed")

        response_times = [r['response_time'] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)

        self.assertLess(avg_response_time, 5.0, f"Average response time: {avg_response_time:.2f}s")
        self.assertLess(max_response_time, 10.0, f"Max response time: {max_response_time:.2f}s")

    def test_concurrent_updates_same_site(self):
        """Test concurrent updates to the same site"""
        # Create initial site
        site = Site.objects.create(
            name="Concurrent Update Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            latitude=15.0,
            longitude=32.0,
            status='active',
            total_population=1000
        )

        # Assign all users to the site
        site.assigned_gsos.set(self.users)

        results = []
        errors = []

        def update_site(user_index):
            """Function to update site concurrently"""
            try:
                user = self.users[user_index]
                client = self.authenticate_client(user)

                update_data = {
                    'total_population': 1000 + user_index * 100
                }

                start_time = time.time()
                response = client.patch(f'/api/mobile/v1/sites/{site.id}/', update_data, format='json')
                end_time = time.time()

                results.append({
                    'user_index': user_index,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == status.HTTP_200_OK,
                    'final_population': response.json().get('total_population') if response.status_code == 200 else None
                })

            except Exception as e:
                errors.append({
                    'user_index': user_index,
                    'error': str(e)
                })

        # Execute concurrent updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_site, i) for i in range(5)]
            for future in futures:
                future.result()

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        success_count = sum(1 for r in results if r['success'])
        self.assertGreater(success_count, 0, "At least some updates should succeed")

        # Verify final state is consistent
        site.refresh_from_db()
        self.assertGreater(site.total_population, 1000, "Site should be updated")

    def test_concurrent_sync_operations(self):
        """Test concurrent sync operations performance"""
        # Create sites for syncing
        for i in range(10):
            site = Site.objects.create(
                name=f'Sync Site {i}',
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 50
            )
            site.assigned_gsos.set(self.users[:3])

        results = []
        errors = []

        def perform_sync(user_index):
            """Function to perform sync concurrently"""
            try:
                user = self.users[user_index]
                client = self.authenticate_client(user)

                sync_data = {
                    'data_types': ['sites'],
                    'last_sync': None
                }

                start_time = time.time()
                response = client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
                end_time = time.time()

                results.append({
                    'user_index': user_index,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == status.HTTP_200_OK,
                    'sites_count': len(response.json().get('sites', [])) if response.status_code == 200 else 0
                })

            except Exception as e:
                errors.append({
                    'user_index': user_index,
                    'error': str(e)
                })

        # Execute concurrent syncs
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_sync, i) for i in range(5)]
            for future in futures:
                future.result()

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        success_count = sum(1 for r in results if r['success'])
        self.assertEqual(success_count, 5, "All syncs should succeed")

        response_times = [r['response_time'] for r in results if r['success']]
        avg_response_time = statistics.mean(response_times)

        self.assertLess(avg_response_time, 15.0, f"Average sync time: {avg_response_time:.2f}s")


class LoadTestingScenarios(APITestCase):
    """Simulate realistic load testing scenarios"""

    def setUp(self):
        """Set up load testing"""
        # Create multiple users with different roles
        self.gso_users = []
        self.ngo_users = []

        for i in range(10):
            gso = User.objects.create_user(
                email=f"load_gso{i}@test.com",
                password="test123",
                role="gso",
                is_active=True
            )
            self.gso_users.append(gso)

            ngo = User.objects.create_user(
                email=f"load_ngo{i}@test.com",
                password="test123",
                role="ngo_user",
                is_active=True
            )
            self.ngo_users.append(ngo)

        # Create test data
        self.state = State.objects.create(name="Load Test State", code="LTS")
        self.locality = Locality.objects.create(
            name="Load Test Locality",
            state=self.state,
            code="LTL"
        )
        self.site_type = SiteType.objects.create(
            name="Load Test Type",
            category="camp"
        )

    def test_realistic_field_usage_pattern(self):
        """Test realistic field usage pattern"""
        # Simulate typical field worker pattern:
        # 1. Login
        # 2. Sync data
        # 3. View assigned sites
        # 4. Create/update sites
        # 5. Periodic syncs

        results = []
        errors = []

        def simulate_field_worker(user_index):
            """Simulate typical field worker usage"""
            try:
                user = self.gso_users[user_index]
                client = APIClient()

                # 1. Login
                login_start = time.time()
                login_data = {
                    'email': user.email,
                    'password': 'test123',
                    'device_id': f'field_device_{user_index}',
                    'platform': 'android'
                }
                login_response = client.post('/api/mobile/v1/auth/login/', login_data)
                login_time = time.time() - login_start

                if login_response.status_code != status.HTTP_200_OK:
                    errors.append(f"Login failed for user {user_index}")
                    return

                tokens = login_response.json()
                client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

                # 2. Initial sync
                sync_start = time.time()
                sync_data = {'data_types': ['sites'], 'last_sync': None}
                sync_response = client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
                sync_time = time.time() - sync_start

                # 3. View sites
                sites_start = time.time()
                sites_response = client.get('/api/mobile/v1/sites/')
                sites_time = time.time() - sites_start

                # 4. Create site
                create_start = time.time()
                site_data = {
                    'name': f'Field Site {user_index}',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': 15.0 + user_index * 0.01,
                    'longitude': 32.0 + user_index * 0.01,
                    'status': 'active',
                    'total_population': 100 + user_index * 50
                }
                create_response = client.post('/api/mobile/v1/sites/', site_data, format='json')
                create_time = time.time() - create_start

                # 5. Get profile
                profile_start = time.time()
                profile_response = client.get('/api/mobile/v1/auth/profile/')
                profile_time = time.time() - profile_start

                results.append({
                    'user_index': user_index,
                    'login_time': login_time,
                    'sync_time': sync_time,
                    'sites_time': sites_time,
                    'create_time': create_time,
                    'profile_time': profile_time,
                    'total_time': login_time + sync_time + sites_time + create_time + profile_time,
                    'all_success': all([
                        login_response.status_code == status.HTTP_200_OK,
                        sync_response.status_code == status.HTTP_200_OK,
                        sites_response.status_code == status.HTTP_200_OK,
                        create_response.status_code == status.HTTP_201_CREATED,
                        profile_response.status_code == status.HTTP_200_OK
                    ])
                })

            except Exception as e:
                errors.append(f"Error for user {user_index}: {str(e)}")

        # Execute concurrent field worker simulations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(simulate_field_worker, i) for i in range(5)]
            for future in futures:
                future.result()

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        successful_sessions = [r for r in results if r['all_success']]
        self.assertGreater(len(successful_sessions), 0, "Some sessions should succeed")

        # Performance assertions
        if successful_sessions:
            avg_total_time = statistics.mean([s['total_time'] for s in successful_sessions])
            avg_login_time = statistics.mean([s['login_time'] for s in successful_sessions])
            avg_sync_time = statistics.mean([s['sync_time'] for s in successful_sessions])

            self.assertLess(avg_total_time, 30.0, f"Average total workflow time: {avg_total_time:.2f}s")
            self.assertLess(avg_login_time, 3.0, f"Average login time: {avg_login_time:.2f}s")
            self.assertLess(avg_sync_time, 10.0, f"Average sync time: {avg_sync_time:.2f}s")

    def test_peak_usage_simulation(self):
        """Test system under peak usage conditions"""
        # Simulate peak usage: multiple users performing various operations

        operations_performed = []
        errors = []

        def random_operations(user_index):
            """Perform random operations to simulate realistic usage"""
            try:
                user = self.gso_users[user_index % len(self.gso_users)]
                client = APIClient()

                # Login
                login_data = {
                    'email': user.email,
                    'password': 'test123',
                    'device_id': f'peak_device_{user_index}',
                    'platform': 'android'
                }
                client.post('/api/mobile/v1/auth/login/', login_data)
                tokens = client.post('/api/mobile/v1/auth/login/', login_data).json()
                client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

                # Perform various operations
                operations = [
                    lambda: client.get('/api/mobile/v1/sites/'),
                    lambda: client.get('/api/mobile/v1/sites/summary/'),
                    lambda: client.get('/api/mobile/v1/auth/profile/'),
                    lambda: client.post('/api/mobile/v1/sync/initial/',
                                       {'data_types': ['sites'], 'last_sync': None}, format='json'),
                ]

                for i, operation in enumerate(operations):
                    start_time = time.time()
                    response = operation()
                    end_time = time.time()

                    operations_performed.append({
                        'user_index': user_index,
                        'operation_index': i,
                        'response_time': end_time - start_time,
                        'status_code': response.status_code,
                        'success': 200 <= response.status_code < 300
                    })

            except Exception as e:
                errors.append(f"Error for user {user_index}: {str(e)}")

        # Execute peak load simulation
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(random_operations, i) for i in range(15)]
            for future in futures:
                future.result()

        # Analyze peak load results
        self.assertLess(len(errors), 3, f"Too many errors during peak load: {errors}")

        successful_operations = [op for op in operations_performed if op['success']]
        total_operations = len(operations_performed)
        success_rate = len(successful_operations) / total_operations if total_operations > 0 else 0

        self.assertGreater(success_rate, 0.95, f"Success rate: {success_rate:.2%}")

        if successful_operations:
            response_times = [op['response_time'] for op in successful_operations]
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]

            self.assertLess(avg_response_time, 5.0, f"Average response time: {avg_response_time:.2f}s")
            self.assertLess(p95_response_time, 10.0, f"95th percentile response time: {p95_response_time:.2f}s")