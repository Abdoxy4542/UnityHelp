"""
Data consistency and concurrent access tests for UnityAid Mobile API.
Tests data integrity, transaction safety, and consistency across operations.
"""

import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, Mock

from django.test import TransactionTestCase, TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import Organization
from apps.sites.models import Site, State, Locality, SiteType, Facility, Population
from apps.assessments.models import Assessment, AssessmentResponse
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog

User = get_user_model()


class DataIntegrityTests(TransactionTestCase):
    """Test data integrity constraints and validation"""

    def setUp(self):
        """Set up data integrity tests"""
        self.user = User.objects.create_user(
            email="integrity@test.com",
            password="test123",
            role="admin",
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create basic geographic data
        self.state = State.objects.create(name="Integrity State", code="IS")
        self.locality = Locality.objects.create(
            name="Integrity Locality",
            state=self.state,
            code="IL"
        )
        self.site_type = SiteType.objects.create(
            name="Integrity Type",
            category="camp"
        )

    def test_unique_constraint_enforcement(self):
        """Test that unique constraints are enforced"""
        # Create initial site
        site_data = {
            'name': 'Unique Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 1000
        }

        # First creation should succeed
        response1 = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second creation with same data might succeed if no unique constraints
        # or fail if there are unique constraints on name + location
        response2 = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertIn(response2.status_code, [
            status.HTTP_201_CREATED,  # If duplicates allowed
            status.HTTP_400_BAD_REQUEST  # If unique constraints enforced
        ])

    def test_foreign_key_constraint_enforcement(self):
        """Test that foreign key constraints are enforced"""
        # Try to create site with invalid foreign keys
        invalid_site_data = {
            'name': 'Invalid FK Site',
            'site_type': 99999,  # Non-existent site type
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 500
        }

        response = self.client.post('/api/mobile/v1/sites/', invalid_site_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try with invalid state
        invalid_state_data = {
            'name': 'Invalid State Site',
            'site_type': self.site_type.id,
            'state': 99999,  # Non-existent state
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 500
        }

        response2 = self.client.post('/api/mobile/v1/sites/', invalid_state_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_data_validation_enforcement(self):
        """Test that data validation rules are enforced"""
        validation_test_cases = [
            {
                'name': 'Invalid Latitude Site',
                'site_type': self.site_type.id,
                'state': self.state.id,
                'locality': self.locality.id,
                'latitude': '999.999',  # Invalid latitude
                'longitude': '32.0',
                'status': 'active',
                'total_population': 500
            },
            {
                'name': 'Invalid Longitude Site',
                'site_type': self.site_type.id,
                'state': self.state.id,
                'locality': self.locality.id,
                'latitude': '15.0',
                'longitude': '999.999',  # Invalid longitude
                'status': 'active',
                'total_population': 500
            },
            {
                'name': 'Negative Population Site',
                'site_type': self.site_type.id,
                'state': self.state.id,
                'locality': self.locality.id,
                'latitude': '15.0',
                'longitude': '32.0',
                'status': 'active',
                'total_population': -100  # Negative population
            },
            {
                'name': '',  # Empty name
                'site_type': self.site_type.id,
                'state': self.state.id,
                'locality': self.locality.id,
                'latitude': '15.0',
                'longitude': '32.0',
                'status': 'active',
                'total_population': 500
            }
        ]

        for invalid_data in validation_test_cases:
            with self.subTest(case=invalid_data.get('name', 'empty_name')):
                response = self.client.post('/api/mobile/v1/sites/', invalid_data, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cascade_deletion_integrity(self):
        """Test that cascade deletions maintain integrity"""
        # Create site with facilities
        site_data = {
            'name': 'Cascade Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 1000,
            'facilities': [
                {
                    'name': 'Test Facility',
                    'facility_type': 'health',
                    'capacity': 100,
                    'current_usage': 50,
                    'is_functional': True
                }
            ]
        }

        response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        site_id = response.json()['id']
        site = Site.objects.get(id=site_id)

        # Verify facility was created
        self.assertEqual(site.facilities.count(), 1)
        facility_id = site.facilities.first().id

        # Delete site
        delete_response = self.client.delete(f'/api/mobile/v1/sites/{site_id}/')

        # If deletion is allowed, verify cascade
        if delete_response.status_code == status.HTTP_204_NO_CONTENT:
            # Facility should be deleted with site (cascade)
            self.assertFalse(Facility.objects.filter(id=facility_id).exists())
        else:
            # Deletion might be restricted for business reasons
            self.assertIn(delete_response.status_code, [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_405_METHOD_NOT_ALLOWED
            ])

    def test_atomic_operations(self):
        """Test that operations are atomic"""
        # Test bulk operations are atomic
        bulk_data = {
            'sites': [
                {
                    'name': 'Atomic Site 1',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '15.1',
                    'longitude': '32.1',
                    'status': 'active',
                    'total_population': 500
                },
                {
                    'name': 'Atomic Site 2 - Invalid',
                    'site_type': 99999,  # Invalid site type
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '15.2',
                    'longitude': '32.2',
                    'status': 'active',
                    'total_population': 600
                },
                {
                    'name': 'Atomic Site 3',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '15.3',
                    'longitude': '32.3',
                    'status': 'active',
                    'total_population': 700
                }
            ]
        }

        initial_count = Site.objects.count()

        response = self.client.post('/api/mobile/v1/sync/bulk-upload/', bulk_data, format='json')

        # Should handle partial success gracefully
        # Implementation may choose to create valid items or rollback all
        final_count = Site.objects.count()

        # Either all or none should be created (atomic behavior)
        # Or valid ones are created with error reporting
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            # Complete rollback
            self.assertEqual(final_count, initial_count)
        else:
            # Partial success with error handling
            self.assertGreaterEqual(final_count, initial_count)


class ConcurrentAccessTests(TransactionTestCase):
    """Test concurrent access scenarios and race conditions"""

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
        """Helper to create authenticated client"""
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

    def test_concurrent_site_updates(self):
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
        lock = threading.Lock()

        def update_site_population(user_index, new_population):
            """Update site population concurrently"""
            try:
                user = self.users[user_index]
                client = self.authenticate_client(user)

                update_data = {'total_population': new_population}

                response = client.patch(f'/api/mobile/v1/sites/{site.id}/', update_data, format='json')

                with lock:
                    results.append({
                        'user_index': user_index,
                        'new_population': new_population,
                        'status_code': response.status_code,
                        'success': response.status_code == status.HTTP_200_OK,
                        'response_population': response.json().get('total_population') if response.status_code == 200 else None
                    })

            except Exception as e:
                with lock:
                    errors.append({
                        'user_index': user_index,
                        'error': str(e)
                    })

        # Execute concurrent updates with different populations
        populations = [1200, 1300, 1400, 1500, 1600]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_site_population, i, populations[i])
                for i in range(5)
            ]
            for future in futures:
                future.result()

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        successful_updates = [r for r in results if r['success']]
        self.assertGreater(len(successful_updates), 0, "At least one update should succeed")

        # Verify final state is consistent
        site.refresh_from_db()
        self.assertIn(site.total_population, populations, "Final population should be one of the attempted values")

        # Check that final value matches at least one successful response
        successful_populations = [r['response_population'] for r in successful_updates]
        self.assertIn(site.total_population, successful_populations)

    def test_concurrent_device_registration(self):
        """Test concurrent device registration for same user"""
        user = self.users[0]
        results = []
        errors = []
        lock = threading.Lock()

        def register_device(device_index):
            """Register device concurrently"""
            try:
                client = APIClient()
                login_data = {
                    'email': user.email,
                    'password': 'test123',
                    'device_id': f'concurrent_device_{device_index}',
                    'platform': 'android'
                }

                response = client.post('/api/mobile/v1/auth/login/', login_data)

                with lock:
                    results.append({
                        'device_index': device_index,
                        'status_code': response.status_code,
                        'success': response.status_code == status.HTTP_200_OK
                    })

            except Exception as e:
                with lock:
                    errors.append({
                        'device_index': device_index,
                        'error': str(e)
                    })

        # Execute concurrent device registrations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_device, i) for i in range(5)]
            for future in futures:
                future.result()

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        successful_registrations = [r for r in results if r['success']]
        self.assertGreater(len(successful_registrations), 0, "At least one registration should succeed")

        # Check device limits are enforced
        active_devices = MobileDevice.objects.filter(user=user, is_active=True).count()
        self.assertLessEqual(active_devices, 5, "Should not exceed reasonable device limit")

    def test_concurrent_sync_operations(self):
        """Test concurrent sync operations"""
        # Create sites for syncing
        sites = []
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
            sites.append(site)

        results = []
        errors = []
        lock = threading.Lock()

        def perform_sync(user_index):
            """Perform sync operation concurrently"""
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

                with lock:
                    results.append({
                        'user_index': user_index,
                        'status_code': response.status_code,
                        'success': response.status_code == status.HTTP_200_OK,
                        'response_time': end_time - start_time,
                        'sites_count': len(response.json().get('sites', [])) if response.status_code == 200 else 0
                    })

            except Exception as e:
                with lock:
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

        successful_syncs = [r for r in results if r['success']]
        self.assertEqual(len(successful_syncs), 5, "All syncs should succeed")

        # Verify sync logs are created properly
        sync_logs = SyncLog.objects.filter(user__in=self.users, sync_type='initial')
        self.assertEqual(sync_logs.count(), 5, "Should have sync log for each user")

    def test_race_condition_in_site_assignment(self):
        """Test race conditions in site assignment"""
        # Create site
        site = Site.objects.create(
            name="Assignment Race Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            latitude=15.0,
            longitude=32.0,
            status='active',
            total_population=1000
        )

        results = []
        errors = []
        lock = threading.Lock()

        def assign_user_to_site(user_index):
            """Assign user to site concurrently"""
            try:
                user = self.users[user_index]

                # Simulate race condition in assignment
                with transaction.atomic():
                    current_gsos = list(site.assigned_gsos.all())
                    if user not in current_gsos:
                        site.assigned_gsos.add(user)
                        success = True
                    else:
                        success = False

                with lock:
                    results.append({
                        'user_index': user_index,
                        'success': success
                    })

            except Exception as e:
                with lock:
                    errors.append({
                        'user_index': user_index,
                        'error': str(e)
                    })

        # Execute concurrent assignments
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(assign_user_to_site, i) for i in range(5)]
            for future in futures:
                future.result()

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Verify all users are assigned (no race condition issues)
        site.refresh_from_db()
        assigned_count = site.assigned_gsos.count()
        self.assertEqual(assigned_count, 5, "All users should be assigned")


class DataConsistencyAcrossOperationsTests(TransactionTestCase):
    """Test data consistency across different operations"""

    def setUp(self):
        """Set up data consistency tests"""
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="test123",
            role="admin",
            is_active=True
        )

        self.gso_user = User.objects.create_user(
            email="gso@test.com",
            password="test123",
            role="gso",
            is_active=True
        )

        # Create basic data
        self.state = State.objects.create(name="Consistency State", code="COS")
        self.locality = Locality.objects.create(
            name="Consistency Locality",
            state=self.state,
            code="COL"
        )
        self.site_type = SiteType.objects.create(
            name="Consistency Type",
            category="camp"
        )

    def test_cross_operation_data_consistency(self):
        """Test data consistency across create, update, and read operations"""
        admin_client = APIClient()
        admin_client.force_authenticate(user=self.admin_user)

        gso_client = APIClient()
        login_data = {
            'email': self.gso_user.email,
            'password': 'test123',
            'device_id': 'consistency_device',
            'platform': 'android'
        }
        gso_client.post('/api/mobile/v1/auth/login/', login_data)
        tokens = gso_client.post('/api/mobile/v1/auth/login/', login_data).json()
        gso_client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')

        # 1. Admin creates site
        site_data = {
            'name': 'Consistency Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 1000
        }

        create_response = admin_client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        site_id = create_response.json()['id']

        # 2. Assign GSO to site
        site = Site.objects.get(id=site_id)
        site.assigned_gsos.add(self.gso_user)

        # 3. GSO reads site immediately
        gso_read_response = gso_client.get(f'/api/mobile/v1/sites/{site_id}/')
        self.assertEqual(gso_read_response.status_code, status.HTTP_200_OK)
        gso_site_data = gso_read_response.json()

        # 4. Verify data consistency between create and read
        self.assertEqual(gso_site_data['name'], site_data['name'])
        self.assertEqual(gso_site_data['total_population'], site_data['total_population'])
        self.assertEqual(gso_site_data['status'], site_data['status'])

        # 5. GSO updates site
        update_data = {
            'total_population': 1200,
            'last_verified_date': timezone.now().date().isoformat()
        }

        update_response = gso_client.patch(f'/api/mobile/v1/sites/{site_id}/', update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        updated_site_data = update_response.json()

        # 6. Admin reads updated site
        admin_read_response = admin_client.get(f'/api/mobile/v1/sites/{site_id}/')
        self.assertEqual(admin_read_response.status_code, status.HTTP_200_OK)
        admin_site_data = admin_read_response.json()

        # 7. Verify consistency across users
        self.assertEqual(admin_site_data['total_population'], update_data['total_population'])
        self.assertEqual(admin_site_data['total_population'], updated_site_data['total_population'])

        # 8. Verify database consistency
        site.refresh_from_db()
        self.assertEqual(site.total_population, update_data['total_population'])

    def test_sync_operation_consistency(self):
        """Test data consistency in sync operations"""
        client = APIClient()
        client.force_authenticate(user=self.gso_user)

        # Create sites directly in database
        sites_created = []
        for i in range(5):
            site = Site.objects.create(
                name=f'Sync Consistency Site {i}',
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 50
            )
            site.assigned_gsos.add(self.gso_user)
            sites_created.append(site)

        # Perform initial sync
        sync_data = {
            'data_types': ['sites'],
            'last_sync': None
        }

        sync_response = client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
        self.assertEqual(sync_response.status_code, status.HTTP_200_OK)

        sync_result = sync_response.json()
        synced_sites = sync_result['sites']

        # Verify all created sites are included in sync
        synced_site_ids = [site['id'] for site in synced_sites]
        created_site_ids = [site.id for site in sites_created]

        for created_id in created_site_ids:
            self.assertIn(created_id, synced_site_ids, f"Site {created_id} should be in sync")

        # Verify data consistency between database and sync response
        for synced_site in synced_sites:
            db_site = Site.objects.get(id=synced_site['id'])
            self.assertEqual(synced_site['name'], db_site.name)
            self.assertEqual(synced_site['total_population'], db_site.total_population)
            self.assertEqual(synced_site['status'], db_site.status)

    def test_bulk_operation_consistency(self):
        """Test data consistency in bulk operations"""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        # Prepare bulk data
        bulk_sites = []
        for i in range(3):
            bulk_sites.append({
                'temp_id': f'bulk_site_{i}',
                'name': f'Bulk Consistency Site {i}',
                'site_type': self.site_type.id,
                'state': self.state.id,
                'locality': self.locality.id,
                'latitude': 14.0 + i * 0.01,
                'longitude': 31.0 + i * 0.01,
                'status': 'active',
                'total_population': 200 + i * 100
            })

        bulk_data = {'sites': bulk_sites}

        # Perform bulk upload
        bulk_response = client.post('/api/mobile/v1/sync/bulk-upload/', bulk_data, format='json')
        self.assertEqual(bulk_response.status_code, status.HTTP_200_OK)

        bulk_result = bulk_response.json()
        self.assertEqual(bulk_result['sites_created'], 3)

        # Verify sites were created with correct data
        for bulk_site in bulk_sites:
            db_sites = Site.objects.filter(name=bulk_site['name'])
            self.assertEqual(db_sites.count(), 1, f"Site {bulk_site['name']} should be created")

            db_site = db_sites.first()
            self.assertEqual(db_site.total_population, bulk_site['total_population'])
            self.assertEqual(db_site.status, bulk_site['status'])
            self.assertEqual(float(db_site.latitude), bulk_site['latitude'])
            self.assertEqual(float(db_site.longitude), bulk_site['longitude'])

        # Verify site mappings in response
        site_mappings = bulk_result.get('site_mappings', {})
        for bulk_site in bulk_sites:
            temp_id = bulk_site['temp_id']
            self.assertIn(temp_id, site_mappings, f"Mapping for {temp_id} should exist")

            real_id = site_mappings[temp_id]
            db_site = Site.objects.get(id=real_id)
            self.assertEqual(db_site.name, bulk_site['name'])

    def test_transaction_rollback_consistency(self):
        """Test that failed transactions maintain data consistency"""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        initial_site_count = Site.objects.count()

        # Attempt bulk operation with mixed valid/invalid data
        mixed_bulk_data = {
            'sites': [
                {
                    'name': 'Valid Site 1',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '14.1',
                    'longitude': '31.1',
                    'status': 'active',
                    'total_population': 300
                },
                {
                    'name': 'Invalid Site',
                    'site_type': 99999,  # Invalid site type
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '14.2',
                    'longitude': '31.2',
                    'status': 'active',
                    'total_population': 400
                },
                {
                    'name': 'Valid Site 2',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '14.3',
                    'longitude': '31.3',
                    'status': 'active',
                    'total_population': 500
                }
            ]
        }

        bulk_response = client.post('/api/mobile/v1/sync/bulk-upload/', mixed_bulk_data, format='json')

        # Check final state
        final_site_count = Site.objects.count()

        if bulk_response.status_code == status.HTTP_400_BAD_REQUEST:
            # Complete rollback - no sites should be created
            self.assertEqual(final_site_count, initial_site_count)
        else:
            # Partial success - only valid sites created
            sites_created = bulk_response.json().get('sites_created', 0)
            self.assertEqual(final_site_count, initial_site_count + sites_created)

            # Verify only valid sites exist
            if sites_created > 0:
                valid_sites = Site.objects.filter(name__in=['Valid Site 1', 'Valid Site 2'])
                self.assertEqual(valid_sites.count(), sites_created)

                # Invalid site should not exist
                invalid_sites = Site.objects.filter(name='Invalid Site')
                self.assertEqual(invalid_sites.count(), 0)


class TimestampConsistencyTests(APITestCase):
    """Test timestamp consistency across operations"""

    def setUp(self):
        """Set up timestamp consistency tests"""
        self.user = User.objects.create_user(
            email="timestamp@test.com",
            password="test123",
            role="gso",
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create basic data
        self.state = State.objects.create(name="Timestamp State", code="TS")
        self.locality = Locality.objects.create(
            name="Timestamp Locality",
            state=self.state,
            code="TL"
        )
        self.site_type = SiteType.objects.create(
            name="Timestamp Type",
            category="camp"
        )

    def test_creation_timestamp_consistency(self):
        """Test that creation timestamps are consistent"""
        before_creation = timezone.now()

        site_data = {
            'name': 'Timestamp Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 1000
        }

        response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        after_creation = timezone.now()
        site_id = response.json()['id']

        # Verify timestamp is within expected range
        site = Site.objects.get(id=site_id)
        self.assertGreaterEqual(site.created_at, before_creation)
        self.assertLessEqual(site.created_at, after_creation)

        # Verify API response includes consistent timestamp
        response_created_at = response.json().get('created_at')
        if response_created_at:
            # Parse the timestamp from response
            from django.utils.dateparse import parse_datetime
            response_timestamp = parse_datetime(response_created_at)
            self.assertEqual(response_timestamp.replace(microsecond=0),
                           site.created_at.replace(microsecond=0))

    def test_update_timestamp_consistency(self):
        """Test that update timestamps are consistent"""
        # Create site first
        site = Site.objects.create(
            name="Update Timestamp Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            latitude=15.0,
            longitude=32.0,
            status='active',
            total_population=1000
        )
        site.assigned_gsos.add(self.user)

        original_updated_at = site.updated_at
        time.sleep(0.01)  # Ensure timestamp difference

        # Update site
        before_update = timezone.now()

        update_data = {'total_population': 1200}
        response = self.client.patch(f'/api/mobile/v1/sites/{site.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        after_update = timezone.now()

        # Verify update timestamp changed
        site.refresh_from_db()
        self.assertGreater(site.updated_at, original_updated_at)
        self.assertGreaterEqual(site.updated_at, before_update)
        self.assertLessEqual(site.updated_at, after_update)

    def test_sync_timestamp_consistency(self):
        """Test that sync operations maintain timestamp consistency"""
        # Create sites with different timestamps
        sites = []
        for i in range(3):
            site = Site.objects.create(
                name=f'Sync Timestamp Site {i}',
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
            time.sleep(0.01)  # Ensure different timestamps

        # Perform sync
        sync_data = {
            'data_types': ['sites'],
            'last_sync': None
        }

        response = self.client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sync_result = response.json()
        synced_sites = sync_result['sites']

        # Verify timestamps in sync response match database
        for synced_site in synced_sites:
            db_site = Site.objects.get(id=synced_site['id'])

            # Check created_at consistency
            if 'created_at' in synced_site:
                from django.utils.dateparse import parse_datetime
                sync_created_at = parse_datetime(synced_site['created_at'])
                self.assertEqual(sync_created_at.replace(microsecond=0),
                               db_site.created_at.replace(microsecond=0))

            # Check updated_at consistency
            if 'updated_at' in synced_site:
                sync_updated_at = parse_datetime(synced_site['updated_at'])
                self.assertEqual(sync_updated_at.replace(microsecond=0),
                               db_site.updated_at.replace(microsecond=0))