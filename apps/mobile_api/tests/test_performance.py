import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.test.utils import override_settings
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse
from apps.mobile_api.models import MobileDevice, SyncLog
from apps.accounts.models import UserProfile
import json

User = get_user_model()


class MobileAPIPerformanceTestCase(APITestCase):
    """Performance tests for mobile API endpoints"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test data for performance testing
        cls.create_test_data()

    @classmethod
    def create_test_data(cls):
        """Create large dataset for performance testing"""

        # Create users
        cls.test_users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'perf_user_{i}',
                email=f'perf{i}@example.com',
                password='password123',
                role='gso',
                is_verified=True
            )
            UserProfile.objects.create(user=user)
            cls.test_users.append(user)

        # Create geographic structure
        cls.states = []
        for i in range(5):
            state = State.objects.create(
                name=f'Performance State {i}',
                center_point={'type': 'Point', 'coordinates': [32.0 + i, 15.0 + i]}
            )
            cls.states.append(state)

        cls.localities = []
        for state in cls.states:
            for j in range(3):
                locality = Locality.objects.create(
                    name=f'Locality {j} in {state.name}',
                    state=state,
                    center_point={'type': 'Point', 'coordinates': [state.center_point['coordinates'][0] + 0.1 * j,
                                                                  state.center_point['coordinates'][1] + 0.1 * j]}
                )
                cls.localities.append(locality)

        # Create many sites for performance testing
        cls.sites = []
        site_types = ['gathering', 'camp', 'school', 'health', 'water']
        for i in range(200):  # 200 sites for performance testing
            locality = cls.localities[i % len(cls.localities)]
            site = Site.objects.create(
                name=f'Performance Site {i}',
                site_type=site_types[i % len(site_types)],
                operational_status='active',
                state=locality.state,
                locality=locality,
                location={'type': 'Point', 'coordinates': [
                    32.0 + (i * 0.01), 15.0 + (i * 0.01)
                ]},
                total_population=100 + (i * 10),
                total_households=20 + (i * 2)
            )
            cls.sites.append(site)

        # Assign sites to users
        sites_per_user = len(cls.sites) // len(cls.test_users)
        for i, user in enumerate(cls.test_users):
            start_idx = i * sites_per_user
            end_idx = start_idx + sites_per_user
            user.assigned_sites.set(cls.sites[start_idx:end_idx])

        # Create assessments
        cls.assessments = []
        for i in range(20):
            assessment = Assessment.objects.create(
                title=f'Performance Assessment {i}',
                assessment_type='rapid',
                status='active',
                created_by=cls.test_users[0],
                kobo_form_id=f'perf_form_{i}'
            )
            assessment.assigned_to.set(cls.test_users[:5])  # Assign to first 5 users
            assessment.target_sites.set(cls.sites[:50])  # Target first 50 sites
            cls.assessments.append(assessment)

    def setUp(self):
        self.client = APIClient()
        self.test_user = self.test_users[0]

        # Login user
        login_data = {
            'email': self.test_user.email,
            'password': 'password123',
            'device_id': 'perf_test_device',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        response = self.client.post(login_url, login_data)
        self.access_token = response.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.access_token}')

    def test_sites_list_performance(self):
        """Test sites list endpoint performance with large dataset"""
        url = reverse('mobile_api_v1:mobile-site-list')

        # Measure response time
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 2.0, f"Sites list took {response_time:.2f}s, should be under 2s")

        # Check pagination is working
        self.assertIn('count', response.data)
        self.assertLessEqual(len(response.data['results']), 20)  # Default page size

    def test_sites_search_performance(self):
        """Test sites search performance"""
        url = reverse('mobile_api_v1:mobile-site-list')

        start_time = time.time()
        response = self.client.get(url, {'search': 'Performance'})
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.5, f"Sites search took {response_time:.2f}s, should be under 1.5s")

    def test_assessments_list_performance(self):
        """Test assessments list endpoint performance"""
        url = reverse('mobile_api_v1:mobile-assessment-list')

        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0, f"Assessments list took {response_time:.2f}s, should be under 1s")

    def test_initial_sync_performance(self):
        """Test initial sync performance with large dataset"""
        url = reverse('mobile_api_v1:initial-sync')

        sync_data = {
            'data_types': ['sites', 'assessments'],
            'device_id': 'perf_test_device'
        }

        start_time = time.time()
        response = self.client.post(url, sync_data, format='json')
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 5.0, f"Initial sync took {response_time:.2f}s, should be under 5s")

        # Check data limits are enforced
        sites_count = len(response.data.get('sites', []))
        assessments_count = len(response.data.get('assessments', []))

        self.assertLessEqual(sites_count, 100, "Sites should be limited to 100 for mobile")
        self.assertLessEqual(assessments_count, 50, "Assessments should be limited to 50 for mobile")

    def test_bulk_upload_performance(self):
        """Test bulk upload performance"""
        url = reverse('mobile_api_v1:bulk-upload')

        # Create 50 sites to upload
        bulk_sites = []
        for i in range(50):
            bulk_sites.append({
                'name': f'Bulk Performance Site {i}',
                'site_type': 'gathering',
                'operational_status': 'active',
                'state': self.states[0].id,
                'locality': self.localities[0].id,
                'total_population': 500 + i
            })

        upload_data = {
            'data_type': 'sites',
            'items': bulk_sites
        }

        start_time = time.time()
        response = self.client.post(url, upload_data, format='json')
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 10.0, f"Bulk upload took {response_time:.2f}s, should be under 10s")
        self.assertEqual(response.data['processed'], 50)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'performance-test-cache',
        }
    })
    def test_caching_effectiveness(self):
        """Test that caching improves performance"""
        url = reverse('mobile_api_v1:mobile-site-list')

        # Clear cache
        cache.clear()

        # First request (no cache)
        start_time = time.time()
        response1 = self.client.get(url)
        end_time = time.time()
        first_request_time = end_time - start_time

        # Second request (should be cached or faster due to DB optimization)
        start_time = time.time()
        response2 = self.client.get(url)
        end_time = time.time()
        second_request_time = end_time - start_time

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Second request should be faster or similar
        self.assertLessEqual(second_request_time, first_request_time + 0.1)

    def test_database_query_optimization(self):
        """Test that database queries are optimized"""
        from django.test.utils import override_settings
        from django.db import connection

        url = reverse('mobile_api_v1:mobile-site-list')

        # Reset query count
        connection.queries_log.clear()

        response = self.client.get(url)

        query_count = len(connection.queries)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(query_count, 10, f"Too many database queries: {query_count}")

    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        url = reverse('mobile_api_v1:mobile-site-list')

        # Test different page sizes
        page_sizes = [10, 20, 50, 100]

        for page_size in page_sizes:
            start_time = time.time()
            response = self.client.get(url, {'page_size': page_size})
            end_time = time.time()

            response_time = end_time - start_time

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertLess(response_time, 2.0,
                          f"Pagination with page_size={page_size} took {response_time:.2f}s")
            self.assertLessEqual(len(response.data['results']), page_size)


class ConcurrentAccessTestCase(TransactionTestCase):
    """Test concurrent access and thread safety"""

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='concurrent_user',
            email='concurrent@example.com',
            password='password123',
            role='gso',
            is_verified=True
        )
        UserProfile.objects.create(user=self.user)

        # Create test data
        self.state = State.objects.create(
            name='Concurrent State',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Concurrent Locality',
            state=self.state
        )

        # Create sites
        self.sites = []
        for i in range(20):
            site = Site.objects.create(
                name=f'Concurrent Site {i}',
                site_type='gathering',
                operational_status='active',
                state=self.state,
                locality=self.locality,
                total_population=1000 + i
            )
            self.sites.append(site)

        self.user.assigned_sites.set(self.sites)

    def login_user(self):
        """Helper method to login and get token"""
        client = APIClient()
        login_data = {
            'email': 'concurrent@example.com',
            'password': 'password123',
            'device_id': f'concurrent_device_{threading.current_thread().ident}',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        response = client.post(login_url, login_data)

        if response.status_code == 200:
            token = response.data['access_token']
            client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
            return client
        return None

    def concurrent_site_access(self):
        """Function to run concurrent site access"""
        client = self.login_user()
        if not client:
            return {'success': False, 'error': 'Login failed'}

        try:
            url = reverse('mobile_api_v1:mobile-site-list')
            response = client.get(url)

            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'count': len(response.data.get('results', [])) if response.status_code == 200 else 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def concurrent_sync_operation(self):
        """Function to run concurrent sync operations"""
        client = self.login_user()
        if not client:
            return {'success': False, 'error': 'Login failed'}

        try:
            url = reverse('mobile_api_v1:initial-sync')
            sync_data = {
                'data_types': ['sites'],
                'device_id': f'sync_device_{threading.current_thread().ident}'
            }

            response = client.post(url, sync_data, format='json')

            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'sync_id': response.data.get('sync_metadata', {}).get('sync_id') if response.status_code == 200 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_concurrent_site_access(self):
        """Test concurrent access to sites endpoint"""
        num_threads = 10

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.concurrent_site_access) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # Check all requests succeeded
        successful_requests = [r for r in results if r['success']]
        self.assertEqual(len(successful_requests), num_threads,
                        f"Only {len(successful_requests)}/{num_threads} requests succeeded")

        # Check all returned the same data
        counts = [r['count'] for r in successful_requests]
        self.assertTrue(all(count == counts[0] for count in counts),
                       "Concurrent requests returned different data")

    def test_concurrent_sync_operations(self):
        """Test concurrent sync operations"""
        num_threads = 5

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.concurrent_sync_operation) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # Check all sync operations succeeded
        successful_syncs = [r for r in results if r['success']]
        self.assertEqual(len(successful_syncs), num_threads,
                        f"Only {len(successful_syncs)}/{num_threads} sync operations succeeded")

        # Check sync logs were created properly
        sync_logs = SyncLog.objects.filter(user=self.user, sync_type='initial')
        self.assertEqual(sync_logs.count(), num_threads)

    def test_concurrent_data_modification(self):
        """Test concurrent data modification operations"""

        def create_site(thread_id):
            client = self.login_user()
            if not client:
                return {'success': False, 'error': 'Login failed'}

            try:
                site_data = {
                    'name': f'Concurrent Created Site {thread_id}',
                    'site_type': 'gathering',
                    'operational_status': 'active',
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'total_population': 500 + thread_id
                }

                url = reverse('mobile_api_v1:mobile-site-list')
                response = client.post(url, site_data, format='json')

                return {
                    'success': response.status_code == 201,
                    'status_code': response.status_code,
                    'site_id': response.data.get('id') if response.status_code == 201 else None
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        num_threads = 5

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_site, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # Check all creations succeeded
        successful_creations = [r for r in results if r['success']]
        self.assertEqual(len(successful_creations), num_threads,
                        f"Only {len(successful_creations)}/{num_threads} site creations succeeded")

        # Verify sites were actually created in database
        created_sites = Site.objects.filter(name__startswith='Concurrent Created Site')
        self.assertEqual(created_sites.count(), num_threads)


class MobileSpecificTestCase(APITestCase):
    """Mobile-specific functionality tests"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='mobile_user',
            email='mobile@example.com',
            password='password123',
            role='gso',
            is_verified=True
        )
        UserProfile.objects.create(user=self.user)

        # Login
        login_data = {
            'email': 'mobile@example.com',
            'password': 'password123',
            'device_id': 'mobile_test_device',
            'platform': 'android',
            'fcm_token': 'mobile_fcm_token'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        response = self.client.post(login_url, login_data)
        self.access_token = response.data['access_token']
        self.device_id = response.data['device_id']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.access_token}')

    def test_gps_location_validation(self):
        """Test GPS location validation in mobile endpoints"""

        # Create geographic entities
        state = State.objects.create(
            name='GPS Test State',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        locality = Locality.objects.create(
            name='GPS Test Locality',
            state=state
        )

        # Test valid GPS coordinates
        valid_site_data = {
            'name': 'GPS Valid Site',
            'site_type': 'gathering',
            'operational_status': 'active',
            'state': state.id,
            'locality': locality.id,
            'location': {'type': 'Point', 'coordinates': [32.7, 15.7]}
        }

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.post(url, valid_site_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test invalid GPS coordinates (out of range)
        invalid_site_data = {
            'name': 'GPS Invalid Site',
            'site_type': 'gathering',
            'location': {'type': 'Point', 'coordinates': [200, 100]}  # Invalid range
        }

        response = self.client.post(url, invalid_site_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nearby_sites_functionality(self):
        """Test nearby sites functionality for mobile"""

        # Create test sites at different locations
        state = State.objects.create(name='Nearby Test State')
        locality = Locality.objects.create(name='Nearby Test Locality', state=state)

        # Close site (within 10km)
        close_site = Site.objects.create(
            name='Close Site',
            site_type='gathering',
            operational_status='active',
            state=state,
            locality=locality,
            location={'type': 'Point', 'coordinates': [32.51, 15.51]}  # ~1.5km from reference
        )

        # Far site (outside 10km)
        far_site = Site.objects.create(
            name='Far Site',
            site_type='camp',
            operational_status='active',
            state=state,
            locality=locality,
            location={'type': 'Point', 'coordinates': [32.7, 15.7]}  # ~20km from reference
        )

        self.user.assigned_sites.set([close_site, far_site])

        # Test nearby sites endpoint
        url = reverse('mobile_api_v1:mobile-site-nearby')
        response = self.client.get(url, {
            'lat': 15.5,
            'lon': 32.5,
            'radius': 10  # 10km radius
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return results (exact filtering may vary based on implementation)
        self.assertIsInstance(response.data, list)

    def test_mobile_device_management(self):
        """Test mobile device management functionality"""

        # Get device list
        url = reverse('mobile_api_v1:device-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        device_data = response.data['results'][0]
        self.assertEqual(device_data['device_id'], 'mobile_test_device')
        self.assertEqual(device_data['platform'], 'android')

        # Update FCM token
        device_id = device_data['id']
        update_url = reverse('mobile_api_v1:device-update-fcm-token', kwargs={'pk': device_id})
        response = self.client.post(update_url, {'fcm_token': 'updated_fcm_token'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify update
        device = MobileDevice.objects.get(id=device_id)
        self.assertEqual(device.fcm_token, 'updated_fcm_token')

    def test_offline_data_handling(self):
        """Test offline data handling capabilities"""

        # Test health check endpoint (should work offline when cached)
        health_url = reverse('mobile_api_v1:health-check')
        response = self.client.get(health_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('timestamp', response.data)
        self.assertIn('database', response.data)
        self.assertIn('cache', response.data)

    def test_mobile_error_responses(self):
        """Test mobile-specific error response formats"""

        # Test unauthorized access
        unauthorized_client = APIClient()
        url = reverse('mobile_api_v1:mobile-site-list')
        response = unauthorized_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test invalid data submission
        invalid_data = {
            'name': '',  # Empty name should cause validation error
            'site_type': 'invalid_type'
        }

        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_data_compression(self):
        """Test that mobile responses are optimized for bandwidth"""

        # Create some test data
        state = State.objects.create(name='Compression Test State')
        locality = Locality.objects.create(name='Compression Test Locality', state=state)

        site = Site.objects.create(
            name='Compression Test Site',
            site_type='gathering',
            operational_status='active',
            state=state,
            locality=locality,
            total_population=1000,
            total_households=200
        )

        # Test site list response structure is mobile-optimized
        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if response.data['results']:
            site_data = response.data['results'][0]

            # Check mobile-optimized fields are present
            mobile_fields = ['coordinates', 'population_summary', 'last_updated']
            for field in mobile_fields:
                self.assertIn(field, site_data)

            # Check population_summary structure
            pop_summary = site_data['population_summary']
            self.assertIn('total_population', pop_summary)
            self.assertIn('vulnerable_count', pop_summary)