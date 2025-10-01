from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog
from apps.accounts.models import UserProfile
from datetime import timedelta
import json

User = get_user_model()


class MobileAPIIntegrationTestCase(APITestCase):
    """Integration tests for complete mobile workflows"""

    def setUp(self):
        self.client = APIClient()

        # Create test users with different roles
        self.gso_user = User.objects.create_user(
            username='gso_user',
            email='gso@example.com',
            password='password123',
            role='gso',
            is_verified=True,
            first_name='GSO',
            last_name='User'
        )

        self.ngo_user = User.objects.create_user(
            username='ngo_user',
            email='ngo@example.com',
            password='password123',
            role='ngo_user',
            is_verified=True,
            first_name='NGO',
            last_name='User'
        )

        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='password123',
            role='admin',
            is_verified=True,
            first_name='Admin',
            last_name='User'
        )

        # Create profiles
        for user in [self.gso_user, self.ngo_user, self.admin_user]:
            UserProfile.objects.create(user=user)

        # Create geographic structure
        self.state = State.objects.create(
            name='Khartoum State',
            name_ar='ولاية الخرطوم',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Khartoum Locality',
            name_ar='محلية الخرطوم',
            state=self.state,
            center_point={'type': 'Point', 'coordinates': [32.6, 15.6]}
        )

        # Create sites
        self.site1 = Site.objects.create(
            name='Al-Salam Gathering Site',
            name_ar='موقع تجمع السلام',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            location={'type': 'Point', 'coordinates': [32.7, 15.7]},
            total_population=2500,
            total_households=500,
            children_under_18=1000,
            adults_18_59=1200,
            elderly_60_plus=300,
            male_count=1300,
            female_count=1200
        )

        self.site2 = Site.objects.create(
            name='Unity Camp',
            site_type='camp',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            location={'type': 'Point', 'coordinates': [32.8, 15.8]},
            total_population=3000,
            total_households=600
        )

        # Assign sites to GSO user
        self.gso_user.assigned_sites.add(self.site1, self.site2)

        # Create assessments
        self.assessment = Assessment.objects.create(
            title='Rapid Needs Assessment - Khartoum',
            title_ar='تقييم سريع للاحتياجات - الخرطوم',
            description='Comprehensive needs assessment for IDP sites',
            assessment_type='rapid',
            status='active',
            created_by=self.admin_user,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=14)).date(),
            kobo_form_id='khartoum_needs_2024',
            kobo_form_url='https://kf.kobotoolbox.org/forms/khartoum_needs_2024'
        )

        # Assign assessment
        self.assessment.assigned_to.add(self.gso_user)
        self.assessment.target_sites.add(self.site1, self.site2)

    def test_complete_mobile_workflow_gso(self):
        """Test complete workflow for GSO user: login -> sync -> assessment -> submit"""

        # Step 1: Mobile Login
        login_data = {
            'email': 'gso@example.com',
            'password': 'password123',
            'device_id': 'gso_device_123',
            'platform': 'android',
            'fcm_token': 'gso_fcm_token_456',
            'app_version': '1.0.0',
            'os_version': 'Android 12',
            'device_model': 'Samsung Galaxy S21'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        login_response = self.client.post(login_url, login_data)

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', login_response.data)
        self.assertIn('refresh_token', login_response.data)

        access_token = login_response.data['access_token']
        refresh_token = login_response.data['refresh_token']
        device_id = login_response.data['device_id']

        # Verify device was created
        device = MobileDevice.objects.get(id=device_id)
        self.assertEqual(device.device_id, 'gso_device_123')
        self.assertEqual(device.platform, 'android')

        # Step 2: Initial Sync
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {access_token}')

        sync_data = {
            'data_types': ['sites', 'assessments'],
            'device_id': device_id
        }

        sync_url = reverse('mobile_api_v1:initial-sync')
        sync_response = self.client.post(sync_url, sync_data, format='json')

        self.assertEqual(sync_response.status_code, status.HTTP_200_OK)
        self.assertIn('sites', sync_response.data)
        self.assertIn('assessments', sync_response.data)

        # Verify GSO sees assigned sites
        sites_data = sync_response.data['sites']
        site_ids = [site['id'] for site in sites_data]
        self.assertIn(self.site1.id, site_ids)
        self.assertIn(self.site2.id, site_ids)

        # Verify GSO sees assigned assessments
        assessments_data = sync_response.data['assessments']
        self.assertEqual(len(assessments_data), 1)
        self.assertEqual(assessments_data[0]['id'], self.assessment.id)

        # Step 3: Get Assessment Form Data
        form_url = reverse('mobile_api_v1:mobile-assessment-form-data', kwargs={'pk': self.assessment.id})
        form_response = self.client.get(form_url)

        self.assertEqual(form_response.status_code, status.HTTP_200_OK)
        self.assertEqual(form_response.data['form_id'], 'khartoum_needs_2024')

        # Step 4: Create Assessment Response
        response_data = {
            'assessment': self.assessment.id,
            'site': self.site1.id,
            'kobo_data': {
                'water_access': 'limited',
                'food_security': 'inadequate',
                'shelter_condition': 'poor',
                'health_services': 'unavailable',
                'education_facilities': 'none',
                'protection_concerns': ['gender_based_violence', 'child_labor']
            },
            'gps_location': {'type': 'Point', 'coordinates': [32.7001, 15.7001]}
        }

        response_url = reverse('mobile_api_v1:mobile-assessment-response-list')
        create_response = self.client.post(response_url, response_data, format='json')

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        response_id = create_response.data['id']

        # Step 5: Update Response (simulate offline editing)
        update_data = {
            'kobo_data': {
                'water_access': 'limited',
                'food_security': 'inadequate',
                'shelter_condition': 'poor',
                'health_services': 'basic_available',  # Updated
                'education_facilities': 'temporary_setup',  # Updated
                'protection_concerns': ['gender_based_violence', 'child_labor'],
                'additional_notes': 'Mobile clinic visits twice a week'  # Added
            }
        }

        update_url = reverse('mobile_api_v1:mobile-assessment-response-detail', kwargs={'pk': response_id})
        update_response = self.client.patch(update_url, update_data, format='json')

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # Step 6: Submit Response
        submit_url = reverse('mobile_api_v1:mobile-assessment-response-submit', kwargs={'pk': response_id})
        submit_response = self.client.post(submit_url)

        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)

        # Verify submission
        assessment_response = AssessmentResponse.objects.get(id=response_id)
        self.assertTrue(assessment_response.is_submitted)
        self.assertIsNotNone(assessment_response.submitted_at)

        # Step 7: Get Dashboard Data
        dashboard_url = reverse('mobile_api_v1:mobile-dashboard-list')
        dashboard_response = self.client.get(dashboard_url)

        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertIn('user_info', dashboard_response.data)
        self.assertIn('statistics', dashboard_response.data)
        self.assertIn('recent_activities', dashboard_response.data)

    def test_cross_app_data_consistency(self):
        """Test data consistency across apps after mobile operations"""

        # Login as GSO
        login_data = {
            'email': 'gso@example.com',
            'password': 'password123',
            'device_id': 'consistency_test_device',
            'platform': 'ios'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data['access_token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {access_token}')

        # Create a new site via mobile API
        site_data = {
            'name': 'New Mobile Site',
            'name_ar': 'موقع محمول جديد',
            'site_type': 'health',
            'operational_status': 'active',
            'state': self.state.id,
            'locality': self.locality.id,
            'location': {'type': 'Point', 'coordinates': [32.9, 15.9]},
            'total_population': 1800,
            'total_households': 360,
            'contact_person': 'Dr. Ahmed Hassan',
            'contact_phone': '+249123456789'
        }

        sites_url = reverse('mobile_api_v1:mobile-site-list')
        site_response = self.client.post(sites_url, site_data, format='json')

        self.assertEqual(site_response.status_code, status.HTTP_201_CREATED)
        new_site_id = site_response.data['id']

        # Verify site exists in main sites model
        new_site = Site.objects.get(id=new_site_id)
        self.assertEqual(new_site.name, 'New Mobile Site')
        self.assertEqual(new_site.total_population, 1800)

        # Create assessment response for new site
        response_data = {
            'assessment': self.assessment.id,
            'site': new_site_id,
            'kobo_data': {'basic_needs': 'adequate', 'water_quality': 'good'},
            'gps_location': {'type': 'Point', 'coordinates': [32.9001, 15.9001]}
        }

        response_url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response_create = self.client.post(response_url, response_data, format='json')

        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)

        # Verify response exists and is linked correctly
        assessment_response = AssessmentResponse.objects.get(id=response_create.data['id'])
        self.assertEqual(assessment_response.site.id, new_site_id)
        self.assertEqual(assessment_response.assessment.id, self.assessment.id)
        self.assertEqual(assessment_response.respondent, self.gso_user)

    def test_role_based_data_access_integration(self):
        """Test that different user roles see appropriate data across all endpoints"""

        # Test NGO User Access
        ngo_login_data = {
            'email': 'ngo@example.com',
            'password': 'password123',
            'device_id': 'ngo_device_456',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        ngo_login = self.client.post(login_url, ngo_login_data)
        ngo_token = ngo_login.data['access_token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {ngo_token}')

        # NGO user should see all active sites
        sites_url = reverse('mobile_api_v1:mobile-site-list')
        ngo_sites = self.client.get(sites_url)

        self.assertEqual(ngo_sites.status_code, status.HTTP_200_OK)
        ngo_site_count = len(ngo_sites.data['results'])

        # NGO user should see active assessments but not be assigned
        assessments_url = reverse('mobile_api_v1:mobile-assessment-list')
        ngo_assessments = self.client.get(assessments_url)

        self.assertEqual(ngo_assessments.status_code, status.HTTP_200_OK)
        if len(ngo_assessments.data['results']) > 0:
            self.assertFalse(ngo_assessments.data['results'][0]['assigned_to_me'])

        # Test GSO User Access
        gso_login_data = {
            'email': 'gso@example.com',
            'password': 'password123',
            'device_id': 'gso_device_789',
            'platform': 'ios'
        }

        gso_login = self.client.post(login_url, gso_login_data)
        gso_token = gso_login.data['access_token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {gso_token}')

        # GSO user should see assigned sites and those in their state
        gso_sites = self.client.get(sites_url)
        self.assertEqual(gso_sites.status_code, status.HTTP_200_OK)

        # GSO user should see assignments
        my_assignments_url = reverse('mobile_api_v1:mobile-assessment-my-assignments')
        gso_assignments = self.client.get(my_assignments_url)

        self.assertEqual(gso_assignments.status_code, status.HTTP_200_OK)
        self.assertEqual(len(gso_assignments.data), 1)
        self.assertEqual(gso_assignments.data[0]['id'], self.assessment.id)

    def test_offline_sync_workflow(self):
        """Test complete offline sync workflow"""

        # Login
        login_data = {
            'email': 'gso@example.com',
            'password': 'password123',
            'device_id': 'offline_test_device',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data['access_token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {access_token}')

        # Initial sync to get data
        sync_data = {
            'data_types': ['sites', 'assessments'],
            'device_id': login_response.data['device_id']
        }

        sync_url = reverse('mobile_api_v1:initial-sync')
        initial_sync = self.client.post(sync_url, sync_data, format='json')

        self.assertEqual(initial_sync.status_code, status.HTTP_200_OK)

        # Simulate offline data collection (bulk upload)
        offline_sites = [
            {
                'name': 'Offline Site 1',
                'site_type': 'gathering',
                'operational_status': 'active',
                'state': self.state.id,
                'locality': self.locality.id,
                'total_population': 500
            },
            {
                'name': 'Offline Site 2',
                'site_type': 'camp',
                'operational_status': 'planned',
                'state': self.state.id,
                'locality': self.locality.id,
                'total_population': 750
            }
        ]

        bulk_upload_data = {
            'data_type': 'sites',
            'items': offline_sites
        }

        bulk_url = reverse('mobile_api_v1:bulk-upload')
        bulk_response = self.client.post(bulk_url, bulk_upload_data, format='json')

        self.assertEqual(bulk_response.status_code, status.HTTP_200_OK)
        self.assertEqual(bulk_response.data['processed'], 2)
        self.assertEqual(bulk_response.data['failed'], 0)

        # Verify sites were created
        self.assertTrue(Site.objects.filter(name='Offline Site 1').exists())
        self.assertTrue(Site.objects.filter(name='Offline Site 2').exists())

        # Check sync log
        sync_log = SyncLog.objects.filter(
            user=self.gso_user,
            sync_type='upload'
        ).order_by('-started_at').first()

        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.status, 'completed')
        self.assertEqual(sync_log.processed_items, 2)

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""

        # Test authentication error recovery
        invalid_login = {
            'email': 'gso@example.com',
            'password': 'wrong_password',
            'device_id': 'error_test_device',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        error_response = self.client.post(login_url, invalid_login)

        self.assertEqual(error_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Successful login after error
        correct_login = {
            'email': 'gso@example.com',
            'password': 'password123',
            'device_id': 'error_test_device',
            'platform': 'android'
        }

        success_response = self.client.post(login_url, correct_login)
        self.assertEqual(success_response.status_code, status.HTTP_200_OK)

        access_token = success_response.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {access_token}')

        # Test data validation error in bulk upload
        invalid_bulk_data = {
            'data_type': 'sites',
            'items': [
                {
                    'name': '',  # Invalid: empty name
                    'site_type': 'invalid_type',  # Invalid type
                    'state': 99999  # Non-existent state
                }
            ]
        }

        bulk_url = reverse('mobile_api_v1:bulk-upload')
        bulk_error = self.client.post(bulk_url, invalid_bulk_data, format='json')

        self.assertEqual(bulk_error.status_code, status.HTTP_200_OK)
        self.assertEqual(bulk_error.data['processed'], 0)
        self.assertEqual(bulk_error.data['failed'], 1)

    def test_concurrent_user_operations(self):
        """Test concurrent operations by multiple users"""

        # Login two users simultaneously
        users_data = [
            ('gso@example.com', 'password123', 'concurrent_gso_device'),
            ('ngo@example.com', 'password123', 'concurrent_ngo_device')
        ]

        tokens = []
        for email, password, device_id in users_data:
            login_data = {
                'email': email,
                'password': password,
                'device_id': device_id,
                'platform': 'android'
            }

            login_url = reverse('mobile_api_v1:mobile-login')
            response = self.client.post(login_url, login_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            tokens.append(response.data['access_token'])

        # Both users perform sync operations
        for i, token in enumerate(tokens):
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

            sync_data = {
                'data_types': ['sites'],
                'device_id': f'concurrent_device_{i}'
            }

            sync_url = reverse('mobile_api_v1:initial-sync')
            sync_response = self.client.post(sync_url, sync_data, format='json')

            self.assertEqual(sync_response.status_code, status.HTTP_200_OK)

        # Verify both sync operations completed successfully
        sync_logs = SyncLog.objects.filter(sync_type='initial').count()
        self.assertGreaterEqual(sync_logs, 2)