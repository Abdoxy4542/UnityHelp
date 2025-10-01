from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse
from apps.mobile_api.models import MobileDevice, SyncLog
from datetime import timedelta

User = get_user_model()


class MobileSyncTestCase(APITestCase):
    """Test mobile sync functionality"""

    def setUp(self):
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='password123',
            role='gso',
            is_verified=True
        )

        # Create mobile device
        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='test_device_123',
            platform='android',
            fcm_token='test_fcm_token'
        )

        # Create geographic entities
        self.state = State.objects.create(
            name='Test State',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Test Locality',
            state=self.state
        )

        # Create test data
        self.site1 = Site.objects.create(
            name='Test Site 1',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            total_population=1000
        )

        self.site2 = Site.objects.create(
            name='Test Site 2',
            site_type='camp',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            total_population=1500
        )

        self.assessment = Assessment.objects.create(
            title='Test Assessment',
            assessment_type='rapid',
            status='active',
            created_by=self.user
        )

        # Assign user to sites and assessments
        self.user.assigned_sites.add(self.site1, self.site2)
        self.assessment.assigned_to.add(self.user)

    def test_initial_sync_success(self):
        """Test successful initial sync"""
        self.client.force_authenticate(user=self.user)

        sync_data = {
            'data_types': ['sites', 'assessments'],
            'device_id': str(self.device.id)
        }

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sites', response.data)
        self.assertIn('assessments', response.data)
        self.assertIn('sync_metadata', response.data)

        # Check if sync log was created
        sync_log = SyncLog.objects.filter(user=self.user, sync_type='initial').first()
        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.status, 'completed')

    def test_initial_sync_default_data_types(self):
        """Test initial sync with default data types"""
        self.client.force_authenticate(user=self.user)

        sync_data = {'device_id': str(self.device.id)}

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sites', response.data)
        self.assertIn('assessments', response.data)

    def test_initial_sync_sites_only(self):
        """Test initial sync requesting only sites"""
        self.client.force_authenticate(user=self.user)

        sync_data = {
            'data_types': ['sites'],
            'device_id': str(self.device.id)
        }

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sites', response.data)
        self.assertNotIn('assessments', response.data)

    def test_initial_sync_gso_permissions(self):
        """Test initial sync respects GSO permissions"""
        self.client.force_authenticate(user=self.user)

        sync_data = {
            'data_types': ['sites'],
            'device_id': str(self.device.id)
        }

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GSO should see assigned sites
        sites_data = response.data['sites']
        site_ids = [site['id'] for site in sites_data]
        self.assertIn(self.site1.id, site_ids)
        self.assertIn(self.site2.id, site_ids)

    def test_incremental_sync(self):
        """Test incremental sync"""
        self.client.force_authenticate(user=self.user)

        # Create a timestamp for last sync
        last_sync = (timezone.now() - timedelta(hours=1)).isoformat()

        sync_data = {
            'last_sync_date': last_sync,
            'data_types': ['sites']
        }

        url = reverse('mobile_api_v1:incremental-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_incremental_sync_missing_date(self):
        """Test incremental sync without last sync date"""
        self.client.force_authenticate(user=self.user)

        url = reverse('mobile_api_v1:incremental-sync')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_upload_sites(self):
        """Test bulk upload of sites data"""
        self.client.force_authenticate(user=self.user)

        sites_data = [
            {
                'name': 'Bulk Site 1',
                'site_type': 'gathering',
                'operational_status': 'active',
                'state': self.state.id,
                'locality': self.locality.id,
                'total_population': 800
            },
            {
                'name': 'Bulk Site 2',
                'site_type': 'camp',
                'operational_status': 'active',
                'state': self.state.id,
                'locality': self.locality.id,
                'total_population': 1200
            }
        ]

        upload_data = {
            'data_type': 'sites',
            'items': sites_data
        }

        url = reverse('mobile_api_v1:bulk-upload')
        response = self.client.post(url, upload_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('processed', response.data)
        self.assertIn('failed', response.data)
        self.assertIn('sync_id', response.data)

        # Verify sites were created
        self.assertTrue(Site.objects.filter(name='Bulk Site 1').exists())
        self.assertTrue(Site.objects.filter(name='Bulk Site 2').exists())

    def test_bulk_upload_invalid_data_type(self):
        """Test bulk upload with invalid data type"""
        self.client.force_authenticate(user=self.user)

        upload_data = {
            'data_type': 'invalid_type',
            'items': []
        }

        url = reverse('mobile_api_v1:bulk-upload')
        response = self.client.post(url, upload_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_upload_empty_items(self):
        """Test bulk upload with empty items list"""
        self.client.force_authenticate(user=self.user)

        upload_data = {
            'data_type': 'sites',
            'items': []
        }

        url = reverse('mobile_api_v1:bulk-upload')
        response = self.client.post(url, upload_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['processed'], 0)
        self.assertEqual(response.data['failed'], 0)

    def test_bulk_upload_partial_failure(self):
        """Test bulk upload with some invalid items"""
        self.client.force_authenticate(user=self.user)

        sites_data = [
            {
                'name': 'Valid Site',
                'site_type': 'gathering',
                'operational_status': 'active',
                'state': self.state.id,
                'locality': self.locality.id
            },
            {
                'name': '',  # Invalid: empty name
                'site_type': 'gathering'
            }
        ]

        upload_data = {
            'data_type': 'sites',
            'items': sites_data
        }

        url = reverse('mobile_api_v1:bulk-upload')
        response = self.client.post(url, upload_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['failed'], 0)

    def test_sync_log_creation(self):
        """Test that sync operations create proper logs"""
        self.client.force_authenticate(user=self.user)

        sync_data = {
            'data_types': ['sites'],
            'device_id': str(self.device.id)
        }

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check sync log
        sync_log = SyncLog.objects.filter(user=self.user).first()
        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.sync_type, 'initial')
        self.assertEqual(sync_log.status, 'completed')
        self.assertGreater(sync_log.total_items, 0)
        self.assertEqual(sync_log.processed_items, sync_log.total_items)

    def test_sync_without_authentication(self):
        """Test sync endpoints require authentication"""
        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sync_metadata_structure(self):
        """Test sync metadata includes required fields"""
        self.client.force_authenticate(user=self.user)

        sync_data = {
            'data_types': ['sites'],
            'device_id': str(self.device.id)
        }

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        metadata = response.data['sync_metadata']
        required_fields = ['sync_id', 'timestamp', 'user_id', 'data_version']
        for field in required_fields:
            self.assertIn(field, metadata)

    def test_sync_performance_limits(self):
        """Test sync respects performance limits"""
        # Create many sites to test limits
        sites = []
        for i in range(150):  # More than the 100 limit
            sites.append(Site(
                name=f'Performance Test Site {i}',
                site_type='gathering',
                operational_status='active',
                state=self.state,
                locality=self.locality
            ))
        Site.objects.bulk_create(sites)

        # Assign all sites to user
        self.user.assigned_sites.set(Site.objects.all())

        self.client.force_authenticate(user=self.user)

        sync_data = {
            'data_types': ['sites'],
            'device_id': str(self.device.id)
        }

        url = reverse('mobile_api_v1:initial-sync')
        response = self.client.post(url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should be limited to 100 sites
        sites_data = response.data['sites']
        self.assertLessEqual(len(sites_data), 100)