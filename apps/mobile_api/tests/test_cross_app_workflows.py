"""
Cross-app integration workflow tests for UnityAid Mobile API.
Tests complete user workflows that span multiple Django apps.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import Organization
from apps.sites.models import Site, State, Locality, Facility, SiteType, Population
from apps.assessments.models import Assessment, AssessmentResponse
from apps.reports.models import Report
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog

User = get_user_model()


class CompleteUserWorkflowTests(APITestCase):
    """Test complete user workflows from mobile login to data collection"""

    def setUp(self):
        """Set up test data for workflow tests"""
        # Create organizations
        self.ngo_org = Organization.objects.create(
            name="Test NGO",
            organization_type="ngo",
            is_active=True
        )

        self.un_org = Organization.objects.create(
            name="Test UN Agency",
            organization_type="un_agency",
            is_active=True
        )

        # Create geographic hierarchy
        self.state = State.objects.create(
            name="Test State",
            name_ar="ولاية تجريبية",
            code="TS"
        )

        self.locality = Locality.objects.create(
            name="Test Locality",
            name_ar="محلية تجريبية",
            state=self.state,
            code="TL"
        )

        # Create site type
        self.site_type = SiteType.objects.create(
            name="IDP Camp",
            category="camp",
            description="Internally Displaced Persons Camp"
        )

        # Create users with different roles
        self.gso_user = User.objects.create_user(
            email="gso@test.com",
            password="test123",
            first_name="GSO",
            last_name="User",
            role="gso",
            organization=self.ngo_org,
            is_active=True
        )

        self.ngo_user = User.objects.create_user(
            email="ngo@test.com",
            password="test123",
            first_name="NGO",
            last_name="User",
            role="ngo_user",
            organization=self.ngo_org,
            is_active=True
        )

        self.cluster_lead = User.objects.create_user(
            email="cluster@test.com",
            password="test123",
            first_name="Cluster",
            last_name="Lead",
            role="cluster_lead",
            organization=self.un_org,
            is_active=True
        )

        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="test123",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
            is_staff=True
        )

        # API client
        self.client = APIClient()

    def authenticate_user(self, user):
        """Helper to authenticate user and return tokens"""
        login_data = {
            'email': user.email,
            'password': 'test123',
            'device_id': f'test_device_{user.id}',
            'platform': 'android'
        }

        response = self.client.post('/api/mobile/v1/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tokens = response.json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {tokens["access_token"]}')
        return tokens

    def test_complete_gso_workflow(self):
        """Test complete GSO workflow: login -> create site -> assessment -> report"""
        # 1. GSO Login
        tokens = self.authenticate_user(self.gso_user)
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)

        # Verify device was created
        device = MobileDevice.objects.get(user=self.gso_user)
        self.assertEqual(device.device_id, f'test_device_{self.gso_user.id}')

        # 2. GSO creates a new site
        site_data = {
            'name': 'Mobile Created Camp',
            'name_ar': 'مخيم تم إنشاؤه بالموبايل',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.123456',
            'longitude': '32.654321',
            'status': 'active',
            'total_population': 1500,
            'facilities': [
                {
                    'name': 'Health Clinic',
                    'facility_type': 'health',
                    'capacity': 100,
                    'current_usage': 80,
                    'is_functional': True
                }
            ]
        }

        site_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(site_response.status_code, status.HTTP_201_CREATED)

        site_id = site_response.json()['id']
        site = Site.objects.get(id=site_id)
        self.assertEqual(site.name, 'Mobile Created Camp')
        self.assertEqual(site.total_population, 1500)
        self.assertTrue(site.assigned_gsos.filter(id=self.gso_user.id).exists())

        # Verify facility was created
        self.assertEqual(site.facilities.count(), 1)
        facility = site.facilities.first()
        self.assertEqual(facility.name, 'Health Clinic')

        # 3. GSO retrieves assessment assignments
        assessments_response = self.client.get('/api/mobile/v1/assessments/my_assignments/')
        self.assertEqual(assessments_response.status_code, status.HTTP_200_OK)

        # 4. GSO checks nearby sites
        nearby_response = self.client.get('/api/mobile/v1/sites/nearby/', {
            'latitude': '15.123456',
            'longitude': '32.654321',
            'radius': '10'
        })
        self.assertEqual(nearby_response.status_code, status.HTTP_200_OK)
        nearby_sites = nearby_response.json()['results']
        self.assertTrue(any(s['id'] == site_id for s in nearby_sites))

        # 5. GSO updates site population
        population_update = {
            'total_population': 1750,
            'demographics': {
                'male': 875,
                'female': 875,
                'children_under_5': 200,
                'elderly_over_60': 150
            }
        }

        update_response = self.client.patch(f'/api/mobile/v1/sites/{site_id}/', population_update, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # Verify update
        site.refresh_from_db()
        self.assertEqual(site.total_population, 1750)

        # 6. GSO creates assessment response (if assessment exists)
        if Assessment.objects.exists():
            assessment = Assessment.objects.first()
            response_data = {
                'assessment': assessment.id,
                'site': site_id,
                'responses': {
                    'population_count': 1750,
                    'needs_assessment': 'high',
                    'water_access': 'limited'
                }
            }

            assessment_response = self.client.post('/api/mobile/v1/assessment-responses/', response_data, format='json')
            self.assertEqual(assessment_response.status_code, status.HTTP_201_CREATED)

    def test_ngo_user_data_access_workflow(self):
        """Test NGO user workflow: login -> view org sites -> sync data"""
        # 1. NGO User Login
        tokens = self.authenticate_user(self.ngo_user)

        # 2. Create a site for the NGO organization first (as admin)
        self.client.force_authenticate(user=self.admin_user)
        site = Site.objects.create(
            name="NGO Managed Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            organization=self.ngo_org,
            latitude=15.5,
            longitude=32.5,
            status='active',
            total_population=800
        )
        site.assigned_gsos.add(self.gso_user)

        # 3. Switch back to NGO user
        self.authenticate_user(self.ngo_user)

        # 4. NGO user views organization sites
        sites_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(sites_response.status_code, status.HTTP_200_OK)

        sites_data = sites_response.json()['results']
        ngo_site_ids = [s['id'] for s in sites_data]
        self.assertIn(site.id, ngo_site_ids)

        # 5. NGO user gets site summary
        summary_response = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)

        summary = summary_response.json()
        self.assertGreater(summary['total_sites'], 0)
        self.assertGreater(summary['total_population'], 0)

        # 6. NGO user performs initial sync
        sync_data = {
            'data_types': ['sites', 'assessments'],
            'last_sync': None
        }

        sync_response = self.client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
        self.assertEqual(sync_response.status_code, status.HTTP_200_OK)

        sync_result = sync_response.json()
        self.assertIn('sites', sync_result)
        self.assertGreater(len(sync_result['sites']), 0)

        # Verify sync log was created
        sync_log = SyncLog.objects.filter(user=self.ngo_user).first()
        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.sync_type, 'initial')
        self.assertEqual(sync_log.status, 'completed')

    def test_cluster_lead_monitoring_workflow(self):
        """Test cluster lead workflow: login -> view regional data -> generate reports"""
        # 1. Cluster Lead Login
        tokens = self.authenticate_user(self.cluster_lead)

        # 2. Create multiple sites in the region (as admin)
        self.client.force_authenticate(user=self.admin_user)

        sites = []
        for i in range(3):
            site = Site.objects.create(
                name=f"Regional Site {i+1}",
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                latitude=15.0 + i * 0.1,
                longitude=32.0 + i * 0.1,
                status='active',
                total_population=500 + i * 200
            )
            sites.append(site)

        # 3. Switch back to cluster lead
        self.authenticate_user(self.cluster_lead)

        # 4. Cluster lead views all regional sites
        sites_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(sites_response.status_code, status.HTTP_200_OK)

        sites_data = sites_response.json()['results']
        self.assertGreaterEqual(len(sites_data), 3)

        # 5. Cluster lead gets comprehensive statistics
        summary_response = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)

        summary = summary_response.json()
        self.assertGreater(summary['total_population'], 1400)  # Sum of all sites

        # 6. Cluster lead performs filtered search
        search_response = self.client.get('/api/mobile/v1/sites/', {
            'search': 'Regional',
            'status': 'active'
        })
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)

        search_results = search_response.json()['results']
        self.assertGreaterEqual(len(search_results), 3)

    def test_admin_bulk_operations_workflow(self):
        """Test admin workflow: login -> bulk operations -> system monitoring"""
        # 1. Admin Login
        tokens = self.authenticate_user(self.admin_user)

        # 2. Admin creates multiple sites via bulk operation
        bulk_sites_data = {
            'sites': [
                {
                    'name': f'Bulk Site {i}',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': 15.0 + i * 0.01,
                    'longitude': 32.0 + i * 0.01,
                    'status': 'active',
                    'total_population': 100 + i * 50
                } for i in range(5)
            ]
        }

        bulk_response = self.client.post('/api/mobile/v1/sync/bulk-upload/', bulk_sites_data, format='json')
        self.assertEqual(bulk_response.status_code, status.HTTP_200_OK)

        bulk_result = bulk_response.json()
        self.assertEqual(bulk_result['sites_created'], 5)

        # 3. Admin views all sites (no role restrictions)
        all_sites_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(all_sites_response.status_code, status.HTTP_200_OK)

        all_sites = all_sites_response.json()['results']
        self.assertGreaterEqual(len(all_sites), 5)

        # 4. Admin checks system-wide statistics
        summary_response = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)

        # 5. Admin performs incremental sync to verify data consistency
        sync_data = {
            'data_types': ['sites'],
            'last_sync': (timezone.now() - timedelta(hours=1)).isoformat()
        }

        sync_response = self.client.post('/api/mobile/v1/sync/incremental/', sync_data, format='json')
        self.assertEqual(sync_response.status_code, status.HTTP_200_OK)

    def test_cross_role_collaboration_workflow(self):
        """Test workflow involving multiple user roles collaborating"""
        # 1. Admin creates initial site structure
        tokens = self.authenticate_user(self.admin_user)

        site_data = {
            'name': 'Collaboration Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.999',
            'longitude': '32.999',
            'status': 'active',
            'total_population': 2000,
            'organization': self.ngo_org.id
        }

        site_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(site_response.status_code, status.HTTP_201_CREATED)
        site_id = site_response.json()['id']

        # Assign GSO to the site
        site = Site.objects.get(id=site_id)
        site.assigned_gsos.add(self.gso_user)

        # 2. GSO user accesses and updates assigned site
        self.authenticate_user(self.gso_user)

        gso_sites_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(gso_sites_response.status_code, status.HTTP_200_OK)

        gso_sites = gso_sites_response.json()['results']
        gso_site_ids = [s['id'] for s in gso_sites]
        self.assertIn(site_id, gso_site_ids)

        # GSO updates population data
        population_update = {
            'total_population': 2200,
            'last_verified_date': timezone.now().date().isoformat()
        }

        gso_update_response = self.client.patch(f'/api/mobile/v1/sites/{site_id}/', population_update, format='json')
        self.assertEqual(gso_update_response.status_code, status.HTTP_200_OK)

        # 3. NGO user (same organization) views updated data
        self.authenticate_user(self.ngo_user)

        ngo_sites_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(ngo_sites_response.status_code, status.HTTP_200_OK)

        ngo_sites = ngo_sites_response.json()['results']
        updated_site = next(s for s in ngo_sites if s['id'] == site_id)
        self.assertEqual(updated_site['total_population'], 2200)

        # 4. Cluster lead views regional overview
        self.authenticate_user(self.cluster_lead)

        cluster_summary_response = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(cluster_summary_response.status_code, status.HTTP_200_OK)

        cluster_summary = cluster_summary_response.json()
        self.assertGreaterEqual(cluster_summary['total_population'], 2200)

    def test_offline_sync_workflow(self):
        """Test offline data collection and sync workflow"""
        # 1. User logs in and syncs initial data
        tokens = self.authenticate_user(self.gso_user)

        initial_sync_data = {
            'data_types': ['sites', 'assessments'],
            'last_sync': None
        }

        initial_sync_response = self.client.post('/api/mobile/v1/sync/initial/', initial_sync_data, format='json')
        self.assertEqual(initial_sync_response.status_code, status.HTTP_200_OK)

        # 2. Simulate offline data collection (sites created offline)
        offline_sites_data = {
            'sites': [
                {
                    'temp_id': 'offline_site_1',
                    'name': 'Offline Created Site 1',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '14.123',
                    'longitude': '31.456',
                    'status': 'active',
                    'total_population': 800,
                    'created_offline': True,
                    'offline_timestamp': timezone.now().isoformat()
                },
                {
                    'temp_id': 'offline_site_2',
                    'name': 'Offline Created Site 2',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '14.456',
                    'longitude': '31.789',
                    'status': 'active',
                    'total_population': 1200,
                    'created_offline': True,
                    'offline_timestamp': timezone.now().isoformat()
                }
            ]
        }

        # 3. User comes back online and uploads offline data
        bulk_upload_response = self.client.post('/api/mobile/v1/sync/bulk-upload/', offline_sites_data, format='json')
        self.assertEqual(bulk_upload_response.status_code, status.HTTP_200_OK)

        upload_result = bulk_upload_response.json()
        self.assertEqual(upload_result['sites_created'], 2)
        self.assertIn('site_mappings', upload_result)

        # 4. Verify offline sites were created with proper assignments
        created_sites = Site.objects.filter(name__startswith='Offline Created Site')
        self.assertEqual(created_sites.count(), 2)

        for site in created_sites:
            self.assertTrue(site.assigned_gsos.filter(id=self.gso_user.id).exists())

        # 5. Perform incremental sync to get latest updates
        incremental_sync_data = {
            'data_types': ['sites'],
            'last_sync': (timezone.now() - timedelta(minutes=30)).isoformat()
        }

        incremental_sync_response = self.client.post('/api/mobile/v1/sync/incremental/', incremental_sync_data, format='json')
        self.assertEqual(incremental_sync_response.status_code, status.HTTP_200_OK)

        # Verify sync log records
        sync_logs = SyncLog.objects.filter(user=self.gso_user).order_by('-created_at')
        self.assertGreaterEqual(sync_logs.count(), 3)  # initial, bulk, incremental

    def test_error_handling_and_recovery_workflow(self):
        """Test error handling and recovery in mobile workflows"""
        # 1. Authenticate user
        tokens = self.authenticate_user(self.gso_user)

        # 2. Test invalid site creation (missing required fields)
        invalid_site_data = {
            'name': 'Invalid Site',
            # Missing required fields
        }

        invalid_response = self.client.post('/api/mobile/v1/sites/', invalid_site_data, format='json')
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

        error_data = invalid_response.json()
        self.assertIn('errors', error_data)

        # 3. Test access to unauthorized site
        # Create site as admin first
        self.client.force_authenticate(user=self.admin_user)
        unauthorized_site = Site.objects.create(
            name="Unauthorized Site",
            site_type=self.site_type,
            state=self.state,
            locality=self.locality,
            latitude=15.0,
            longitude=32.0,
            status='active',
            total_population=500
        )

        # Try to access as GSO (not assigned)
        self.authenticate_user(self.gso_user)
        unauthorized_response = self.client.get(f'/api/mobile/v1/sites/{unauthorized_site.id}/')
        self.assertEqual(unauthorized_response.status_code, status.HTTP_404_NOT_FOUND)

        # 4. Test invalid GPS coordinates
        invalid_gps_data = {
            'name': 'Invalid GPS Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '999.999',  # Invalid latitude
            'longitude': '999.999',  # Invalid longitude
            'status': 'active',
            'total_population': 100
        }

        invalid_gps_response = self.client.post('/api/mobile/v1/sites/', invalid_gps_data, format='json')
        self.assertEqual(invalid_gps_response.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Test token refresh workflow
        refresh_token = RefreshToken.objects.get(user=self.gso_user)

        refresh_data = {
            'refresh_token': refresh_token.token,
            'device_id': f'test_device_{self.gso_user.id}'
        }

        refresh_response = self.client.post('/api/mobile/v1/auth/refresh/', refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

        new_tokens = refresh_response.json()
        self.assertIn('access_token', new_tokens)

        # Use new token for authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {new_tokens["access_token"]}')
        test_response = self.client.get('/api/mobile/v1/sites/')
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)


class DataConsistencyWorkflowTests(TransactionTestCase):
    """Test data consistency across mobile and Django apps"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="consistency@test.com",
            password="test123",
            role="admin",
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create basic geographic data
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

    def test_concurrent_site_updates(self):
        """Test handling of concurrent site updates from mobile and Django"""
        # Create initial site
        site_data = {
            'name': 'Concurrent Test Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.0',
            'longitude': '32.0',
            'status': 'active',
            'total_population': 1000
        }

        site_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(site_response.status_code, status.HTTP_201_CREATED)
        site_id = site_response.json()['id']

        # Simulate concurrent updates
        with transaction.atomic():
            # Update 1: Population increase
            update1_data = {'total_population': 1200}
            response1 = self.client.patch(f'/api/mobile/v1/sites/{site_id}/', update1_data, format='json')
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

        with transaction.atomic():
            # Update 2: Status change
            update2_data = {'status': 'inactive'}
            response2 = self.client.patch(f'/api/mobile/v1/sites/{site_id}/', update2_data, format='json')
            self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify final state
        final_site = Site.objects.get(id=site_id)
        self.assertEqual(final_site.total_population, 1200)
        self.assertEqual(final_site.status, 'inactive')

    def test_database_transaction_integrity(self):
        """Test database transaction integrity in mobile operations"""
        # Test bulk operation with partial failure
        bulk_data = {
            'sites': [
                {
                    'name': 'Valid Site 1',
                    'site_type': self.site_type.id,
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '15.1',
                    'longitude': '32.1',
                    'status': 'active',
                    'total_population': 500
                },
                {
                    'name': 'Invalid Site',
                    'site_type': 99999,  # Invalid site type
                    'state': self.state.id,
                    'locality': self.locality.id,
                    'latitude': '15.2',
                    'longitude': '32.2',
                    'status': 'active',
                    'total_population': 600
                },
                {
                    'name': 'Valid Site 2',
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

        bulk_response = self.client.post('/api/mobile/v1/sync/bulk-upload/', bulk_data, format='json')

        # Should handle partial success gracefully
        self.assertIn(bulk_response.status_code, [status.HTTP_200_OK, status.HTTP_207_MULTI_STATUS])

        # Verify valid sites were created
        valid_sites = Site.objects.filter(name__in=['Valid Site 1', 'Valid Site 2'])
        self.assertGreaterEqual(valid_sites.count(), 1)  # At least some should succeed

    def test_foreign_key_consistency(self):
        """Test foreign key relationships remain consistent across operations"""
        # Create site with facilities
        site_data = {
            'name': 'FK Consistency Site',
            'site_type': self.site_type.id,
            'state': self.state.id,
            'locality': self.locality.id,
            'latitude': '15.5',
            'longitude': '32.5',
            'status': 'active',
            'total_population': 800,
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

        site_response = self.client.post('/api/mobile/v1/sites/', site_data, format='json')
        self.assertEqual(site_response.status_code, status.HTTP_201_CREATED)
        site_id = site_response.json()['id']

        # Verify relationships
        site = Site.objects.get(id=site_id)
        self.assertEqual(site.facilities.count(), 1)
        self.assertEqual(site.state_id, self.state.id)
        self.assertEqual(site.locality_id, self.locality.id)

        # Update site and verify relationships maintained
        update_data = {'total_population': 900}
        update_response = self.client.patch(f'/api/mobile/v1/sites/{site_id}/', update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        site.refresh_from_db()
        self.assertEqual(site.facilities.count(), 1)  # Relationship preserved
        self.assertEqual(site.total_population, 900)  # Update applied


class PerformanceWorkflowTests(APITestCase):
    """Test performance aspects of mobile workflows"""

    def setUp(self):
        """Set up performance test data"""
        self.user = User.objects.create_user(
            email="perf@test.com",
            password="test123",
            role="admin",
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test data
        self.state = State.objects.create(name="Perf State", code="PS")
        self.locality = Locality.objects.create(
            name="Perf Locality",
            state=self.state,
            code="PL"
        )
        self.site_type = SiteType.objects.create(
            name="Perf Type",
            category="camp"
        )

    def test_large_dataset_sync_performance(self):
        """Test sync performance with large datasets"""
        import time

        # Create many sites first
        sites = []
        for i in range(50):  # Reduced for test performance
            site = Site.objects.create(
                name=f'Perf Site {i}',
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 10
            )
            sites.append(site)

        # Test initial sync performance
        start_time = time.time()

        sync_data = {
            'data_types': ['sites'],
            'last_sync': None
        }

        sync_response = self.client.post('/api/mobile/v1/sync/initial/', sync_data, format='json')
        sync_time = time.time() - start_time

        self.assertEqual(sync_response.status_code, status.HTTP_200_OK)
        self.assertLess(sync_time, 10.0)  # Should complete within 10 seconds

        sync_result = sync_response.json()
        self.assertEqual(len(sync_result['sites']), 50)

    def test_pagination_performance(self):
        """Test pagination performance with large result sets"""
        # Create many sites
        for i in range(30):  # Reduced for test performance
            Site.objects.create(
                name=f'Pagination Site {i}',
                site_type=self.site_type,
                state=self.state,
                locality=self.locality,
                latitude=15.0 + i * 0.01,
                longitude=32.0 + i * 0.01,
                status='active',
                total_population=100 + i * 10
            )

        # Test paginated requests
        import time
        start_time = time.time()

        page1_response = self.client.get('/api/mobile/v1/sites/?page=1&page_size=10')
        request_time = time.time() - start_time

        self.assertEqual(page1_response.status_code, status.HTTP_200_OK)
        self.assertLess(request_time, 2.0)  # Should be fast with pagination

        page1_data = page1_response.json()
        self.assertEqual(len(page1_data['results']), 10)
        self.assertIsNotNone(page1_data.get('next'))

    @patch('apps.mobile_api.v1.views.cache')
    def test_caching_performance(self, mock_cache):
        """Test caching improves performance"""
        # Configure mock cache
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        # First request (cache miss)
        response1 = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Verify cache was called
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()

        # Second request (should attempt cache hit)
        mock_cache.get.return_value = {'total_sites': 0, 'total_population': 0}

        response2 = self.client.get('/api/mobile/v1/sites/summary/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify cache get was called again
        self.assertGreaterEqual(mock_cache.get.call_count, 2)