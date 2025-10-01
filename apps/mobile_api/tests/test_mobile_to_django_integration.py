"""
Mobile API → Django Apps Integration Tests

These tests verify that data created/modified through the Mobile API
is properly stored and accessible in Django apps.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db import connection
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.accounts.models import UserProfile
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse
from apps.reports.models import FieldReport
from apps.mobile_api.models import MobileDevice, RefreshToken, SyncLog
from datetime import timedelta

User = get_user_model()


class MobileToDjangoIntegrationTestCase(APITestCase):
    """Test data flows from Mobile API to Django apps"""

    def setUp(self):
        # Create test users
        self.gso_user = User.objects.create_user(
            username='mobile_gso',
            email='mobile_gso@test.com',
            password='gso123',
            role='gso',
            is_verified=True,
            first_name='Mobile',
            last_name='GSO'
        )

        self.admin_user = User.objects.create_superuser(
            username='mobile_admin',
            email='mobile_admin@test.com',
            password='admin123',
            role='admin'
        )

        # Create profiles
        UserProfile.objects.create(user=self.gso_user)
        UserProfile.objects.create(user=self.admin_user)

        # Set up geographic hierarchy
        self.state = State.objects.create(
            name='Mobile Test State',
            name_ar='ولاية اختبار المحمول',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Mobile Test Locality',
            name_ar='محلية اختبار المحمول',
            state=self.state,
            center_point={'type': 'Point', 'coordinates': [32.6, 15.6]}
        )

        # Set up mobile API authentication
        self.mobile_client = APIClient()
        self.mobile_login()

    def mobile_login(self):
        """Login to mobile API"""
        login_data = {
            'email': 'mobile_gso@test.com',
            'password': 'gso123',
            'device_id': 'mobile_to_django_device',
            'platform': 'android',
            'fcm_token': 'test_fcm_token',
            'app_version': '1.0.0',
            'device_model': 'Test Device'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        response = self.mobile_client.post(login_url, login_data)

        if response.status_code == 200:
            self.access_token = response.data['access_token']
            self.device_id = response.data['device_id']
            self.mobile_client.credentials(HTTP_AUTHORIZATION=f'Token {self.access_token}')
            return True
        return False

    def test_mobile_site_creation_to_django_storage(self):
        """Test: Create site via mobile API → Verify Django model storage"""

        # Step 1: Create site via mobile API
        site_data = {
            'name': 'Mobile Created Site',
            'name_ar': 'موقع تم إنشاؤه من المحمول',
            'site_type': 'gathering',
            'operational_status': 'active',
            'state': self.state.id,
            'locality': self.locality.id,
            'location': {'type': 'Point', 'coordinates': [32.7, 15.7]},
            'total_population': 1800,
            'total_households': 360,
            'children_under_18': 720,
            'adults_18_59': 900,
            'elderly_60_plus': 180,
            'male_count': 900,
            'female_count': 900,
            'disabled_count': 45,
            'pregnant_women': 25,
            'chronically_ill': 30,
            'contact_person': 'Mobile Field Officer',
            'contact_phone': '+249987654321',
            'contact_email': 'field@mobile.com',
            'reported_by': 'Mobile Application'
        }

        mobile_sites_url = reverse('mobile_api_v1:mobile-site-list')
        response = self.mobile_client.post(mobile_sites_url, site_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mobile_site_id = response.data['id']

        # Step 2: Verify site exists in Django Site model
        django_site = Site.objects.get(id=mobile_site_id)

        self.assertEqual(django_site.name, 'Mobile Created Site')
        self.assertEqual(django_site.name_ar, 'موقع تم إنشاؤه من المحمول')
        self.assertEqual(django_site.site_type, 'gathering')
        self.assertEqual(django_site.operational_status, 'active')
        self.assertEqual(django_site.state, self.state)
        self.assertEqual(django_site.locality, self.locality)
        self.assertEqual(django_site.total_population, 1800)
        self.assertEqual(django_site.total_households, 360)
        self.assertEqual(django_site.disabled_count, 45)
        self.assertEqual(django_site.pregnant_women, 25)
        self.assertEqual(django_site.chronically_ill, 30)
        self.assertEqual(django_site.contact_person, 'Mobile Field Officer')

        # Step 3: Verify computed properties work correctly
        self.assertEqual(django_site.vulnerability_rate, 5.56)  # (45+25+30)/1800 * 100
        self.assertEqual(django_site.average_household_size, 5.0)  # 1800/360

        # Step 4: Verify location data integrity
        self.assertEqual(django_site.coordinates, [32.7, 15.7])
        self.assertEqual(django_site.longitude, 32.7)
        self.assertEqual(django_site.latitude, 15.7)

    def test_mobile_site_update_to_django_persistence(self):
        """Test: Update site via mobile API → Verify Django model changes"""

        # Step 1: Create initial site
        initial_site = Site.objects.create(
            name='Original Mobile Site',
            site_type='gathering',
            operational_status='planned',
            state=self.state,
            locality=self.locality,
            total_population=1000
        )

        self.gso_user.assigned_sites.add(initial_site)

        # Step 2: Update site via mobile API
        update_data = {
            'name': 'Updated Mobile Site',
            'operational_status': 'active',
            'total_population': 1500,
            'total_households': 300,
            'children_under_18': 600,
            'adults_18_59': 750,
            'elderly_60_plus': 150,
            'contact_person': 'Updated Field Officer',
            'contact_phone': '+249111222333'
        }

        mobile_site_url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': initial_site.id})
        response = self.mobile_client.patch(mobile_site_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 3: Verify Django model reflects all changes
        initial_site.refresh_from_db()

        self.assertEqual(initial_site.name, 'Updated Mobile Site')
        self.assertEqual(initial_site.operational_status, 'active')
        self.assertEqual(initial_site.total_population, 1500)
        self.assertEqual(initial_site.total_households, 300)
        self.assertEqual(initial_site.children_under_18, 600)
        self.assertEqual(initial_site.contact_person, 'Updated Field Officer')
        self.assertEqual(initial_site.contact_phone, '+249111222333')

        # Step 4: Verify updated_at timestamp changed
        self.assertIsNotNone(initial_site.updated_at)

    def test_mobile_assessment_response_to_django_storage(self):
        """Test: Submit assessment response via mobile → Verify Django storage"""

        # Step 1: Create assessment and site via Django
        assessment = Assessment.objects.create(
            title='Mobile Response Test Assessment',
            assessment_type='rapid',
            status='active',
            created_by=self.admin_user,
            kobo_form_id='mobile_test_form'
        )

        target_site = Site.objects.create(
            name='Assessment Target Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        # Assign assessment and site to GSO
        assessment.assigned_to.add(self.gso_user)
        assessment.target_sites.add(target_site)
        self.gso_user.assigned_sites.add(target_site)

        # Step 2: Create assessment response via mobile API
        response_data = {
            'assessment': assessment.id,
            'site': target_site.id,
            'kobo_data': {
                'water_access': 'limited',
                'food_security': 'inadequate',
                'shelter_condition': 'poor',
                'health_services': 'basic_available',
                'education_facilities': 'none',
                'protection_concerns': ['gender_based_violence', 'child_labor'],
                'population_count': 1200,
                'urgent_needs': ['clean_water', 'medical_supplies'],
                'field_notes': 'Situation is deteriorating, immediate assistance needed'
            },
            'gps_location': {'type': 'Point', 'coordinates': [32.7001, 15.7001]}
        }

        mobile_response_url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response = self.mobile_client.post(mobile_response_url, response_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mobile_response_id = response.data['id']

        # Step 3: Verify Django AssessmentResponse model
        django_response = AssessmentResponse.objects.get(id=mobile_response_id)

        self.assertEqual(django_response.assessment, assessment)
        self.assertEqual(django_response.site, target_site)
        self.assertEqual(django_response.respondent, self.gso_user)
        self.assertFalse(django_response.is_submitted)
        self.assertIsNone(django_response.submitted_at)

        # Verify kobo_data integrity
        kobo_data = django_response.kobo_data
        self.assertEqual(kobo_data['water_access'], 'limited')
        self.assertEqual(kobo_data['population_count'], 1200)
        self.assertIn('clean_water', kobo_data['urgent_needs'])
        self.assertEqual(kobo_data['field_notes'], 'Situation is deteriorating, immediate assistance needed')

        # Verify GPS location
        self.assertEqual(django_response.gps_location['coordinates'], [32.7001, 15.7001])

        # Step 4: Submit the response via mobile API
        submit_url = reverse('mobile_api_v1:mobile-assessment-response-submit', kwargs={'pk': mobile_response_id})
        submit_response = self.mobile_client.post(submit_url)

        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)

        # Step 5: Verify Django model reflects submission
        django_response.refresh_from_db()
        self.assertTrue(django_response.is_submitted)
        self.assertIsNotNone(django_response.submitted_at)

    def test_mobile_bulk_upload_to_django_batch_processing(self):
        """Test: Bulk upload via mobile → Verify Django batch processing"""

        # Step 1: Prepare bulk site data
        bulk_sites_data = []
        for i in range(10):
            bulk_sites_data.append({
                'name': f'Bulk Mobile Site {i}',
                'name_ar': f'موقع مجمع محمول {i}',
                'site_type': 'gathering',
                'operational_status': 'active',
                'state': self.state.id,
                'locality': self.locality.id,
                'location': {'type': 'Point', 'coordinates': [32.5 + i * 0.01, 15.5 + i * 0.01]},
                'total_population': 500 + i * 100,
                'total_households': 100 + i * 20,
                'contact_person': f'Field Officer {i}'
            })

        # Step 2: Upload via mobile bulk API
        bulk_data = {
            'data_type': 'sites',
            'items': bulk_sites_data
        }

        bulk_url = reverse('mobile_api_v1:bulk-upload')
        response = self.mobile_client.post(bulk_url, bulk_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['processed'], 10)
        self.assertEqual(response.data['failed'], 0)

        # Step 3: Verify all sites exist in Django
        for i, site_data in enumerate(bulk_sites_data):
            django_site = Site.objects.get(name=f'Bulk Mobile Site {i}')
            self.assertEqual(django_site.total_population, 500 + i * 100)
            self.assertEqual(django_site.contact_person, f'Field Officer {i}')

        # Step 4: Verify sync log was created
        sync_log = SyncLog.objects.filter(
            user=self.gso_user,
            sync_type='upload'
        ).order_by('-started_at').first()

        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.status, 'completed')
        self.assertEqual(sync_log.total_items, 10)
        self.assertEqual(sync_log.processed_items, 10)
        self.assertEqual(sync_log.failed_items, 0)

    def test_mobile_user_profile_updates_to_django_persistence(self):
        """Test: Update user profile via mobile → Verify Django User model"""

        # Step 1: Update profile via mobile API
        profile_data = {
            'first_name': 'Updated Mobile',
            'last_name': 'User',
            'phone_number': '+249123456789',
            'organization': 'Mobile Updated Org',
            'preferred_language': 'ar'
        }

        profile_url = reverse('mobile_api_v1:mobile-profile')
        response = self.mobile_client.patch(profile_url, profile_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 2: Verify Django User model changes
        self.gso_user.refresh_from_db()

        self.assertEqual(self.gso_user.first_name, 'Updated Mobile')
        self.assertEqual(self.gso_user.last_name, 'User')
        self.assertEqual(self.gso_user.phone_number, '+249123456789')
        self.assertEqual(self.gso_user.organization, 'Mobile Updated Org')
        self.assertEqual(self.gso_user.preferred_language, 'ar')

        # Step 3: Verify mobile API reflects changes
        get_response = self.mobile_client.get(profile_url)
        self.assertEqual(get_response.data['full_name'], 'Updated Mobile User')

    def test_mobile_device_registration_to_django_tracking(self):
        """Test: Register device via mobile → Verify Django device tracking"""

        # Step 1: Verify device was created during login
        device = MobileDevice.objects.get(id=self.device_id)

        self.assertEqual(device.user, self.gso_user)
        self.assertEqual(device.device_id, 'mobile_to_django_device')
        self.assertEqual(device.platform, 'android')
        self.assertEqual(device.fcm_token, 'test_fcm_token')
        self.assertEqual(device.app_version, '1.0.0')
        self.assertEqual(device.device_model, 'Test Device')
        self.assertTrue(device.is_active)

        # Step 2: Update FCM token via mobile API
        update_token_url = reverse('mobile_api_v1:device-update-fcm-token', kwargs={'pk': device.id})
        token_response = self.mobile_client.post(update_token_url, {'fcm_token': 'updated_fcm_token'})

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)

        # Step 3: Verify Django model reflects token update
        device.refresh_from_db()
        self.assertEqual(device.fcm_token, 'updated_fcm_token')

    def test_mobile_data_validation_to_django_constraints(self):
        """Test: Mobile API validation → Verify Django model constraints enforced"""

        # Step 1: Attempt to create site with invalid data via mobile API
        invalid_site_data = {
            'name': '',  # Empty name should fail
            'site_type': 'invalid_type',  # Invalid choice
            'state': 99999,  # Non-existent state
            'location': {'type': 'Point', 'coordinates': [200, 100]}  # Invalid coordinates
        }

        mobile_sites_url = reverse('mobile_api_v1:mobile-site-list')
        response = self.mobile_client.post(mobile_sites_url, invalid_site_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Step 2: Verify no invalid site was created in Django
        invalid_sites = Site.objects.filter(name='')
        self.assertEqual(invalid_sites.count(), 0)

        # Step 3: Test GPS coordinate validation
        invalid_gps_data = {
            'name': 'Invalid GPS Site',
            'site_type': 'gathering',
            'operational_status': 'active',
            'state': self.state.id,
            'locality': self.locality.id,
            'location': {'type': 'Point', 'coordinates': [181, 91]}  # Out of valid range
        }

        response = self.mobile_client.post(mobile_sites_url, invalid_gps_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_sync_operations_to_django_logging(self):
        """Test: Mobile sync operations → Verify Django logging and tracking"""

        # Step 1: Perform initial sync via mobile API
        sync_data = {
            'data_types': ['sites', 'assessments'],
            'device_id': self.device_id
        }

        sync_url = reverse('mobile_api_v1:initial-sync')
        response = self.mobile_client.post(sync_url, sync_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 2: Verify SyncLog was created in Django
        sync_log = SyncLog.objects.filter(
            user=self.gso_user,
            sync_type='initial'
        ).order_by('-started_at').first()

        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.sync_type, 'initial')
        self.assertEqual(sync_log.status, 'completed')
        self.assertIsNotNone(sync_log.completed_at)
        self.assertGreater(sync_log.total_items, 0)
        self.assertEqual(sync_log.processed_items, sync_log.total_items)

        # Step 3: Verify sync metadata
        self.assertIsNotNone(sync_log.sync_data)
        self.assertIn('sync_id', response.data['sync_metadata'])

    def test_mobile_offline_data_to_django_conflict_resolution(self):
        """Test: Mobile offline data upload → Verify Django conflict resolution"""

        # Step 1: Create site via Django (simulating server-side change)
        django_site = Site.objects.create(
            name='Conflict Test Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            total_population=1000
        )

        self.gso_user.assigned_sites.add(django_site)

        # Step 2: Simulate mobile offline modification
        mobile_update_data = {
            'total_population': 1200,  # Different from Django version
            'total_households': 240,
            'contact_person': 'Mobile Updated Officer'
        }

        mobile_site_url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': django_site.id})
        response = self.mobile_client.patch(mobile_site_url, mobile_update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 3: Verify Django model reflects mobile changes (last-write-wins)
        django_site.refresh_from_db()
        self.assertEqual(django_site.total_population, 1200)
        self.assertEqual(django_site.total_households, 240)
        self.assertEqual(django_site.contact_person, 'Mobile Updated Officer')

    def test_mobile_database_transaction_integrity(self):
        """Test: Mobile API operations → Verify Django database transaction integrity"""

        # Step 1: Create assessment response with related data
        assessment = Assessment.objects.create(
            title='Transaction Test Assessment',
            assessment_type='rapid',
            status='active',
            created_by=self.admin_user
        )

        site = Site.objects.create(
            name='Transaction Test Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        assessment.assigned_to.add(self.gso_user)
        self.gso_user.assigned_sites.add(site)

        # Step 2: Record initial database state
        initial_response_count = AssessmentResponse.objects.count()

        # Step 3: Create response via mobile API
        response_data = {
            'assessment': assessment.id,
            'site': site.id,
            'kobo_data': {'test': 'data'},
            'gps_location': {'type': 'Point', 'coordinates': [32.7, 15.7]}
        }

        mobile_response_url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response = self.mobile_client.post(mobile_response_url, response_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 4: Verify transaction completed successfully
        final_response_count = AssessmentResponse.objects.count()
        self.assertEqual(final_response_count, initial_response_count + 1)

        # Step 5: Verify foreign key relationships are intact
        created_response = AssessmentResponse.objects.get(id=response.data['id'])
        self.assertEqual(created_response.assessment, assessment)
        self.assertEqual(created_response.site, site)
        self.assertEqual(created_response.respondent, self.gso_user)

class MobileAPIQueryOptimizationTestCase(APITestCase):
    """Test Mobile API → Django database query optimization"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='query_test_user',
            email='query@test.com',
            password='password123',
            role='gso',
            is_verified=True
        )
        UserProfile.objects.create(user=self.user)

        # Login to mobile API
        self.mobile_client = APIClient()
        login_data = {
            'email': 'query@test.com',
            'password': 'password123',
            'device_id': 'query_test_device',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        response = self.mobile_client.post(login_url, login_data)
        token = response.data['access_token']
        self.mobile_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_mobile_api_database_query_efficiency(self):
        """Test: Mobile API operations → Verify efficient Django database queries"""

        # Create test data
        state = State.objects.create(name='Query Test State')
        locality = Locality.objects.create(name='Query Test Locality', state=state)

        # Create multiple sites
        sites = []
        for i in range(20):
            site = Site.objects.create(
                name=f'Query Test Site {i}',
                site_type='gathering',
                operational_status='active',
                state=state,
                locality=locality
            )
            sites.append(site)

        self.user.assigned_sites.set(sites)

        # Track database queries
        with self.assertNumQueries(4):  # Should be optimized to minimal queries
            sites_url = reverse('mobile_api_v1:mobile-site-list')
            response = self.mobile_client.get(sites_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 20)

        # Verify select_related optimization worked
        for site_data in response.data['results'][:5]:
            self.assertIn('state_name', site_data)
            self.assertIn('locality_name', site_data)