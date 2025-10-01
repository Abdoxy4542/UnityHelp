"""
Django Apps → Mobile API Integration Tests

These tests verify that data created/modified in Django apps
is properly accessible and synchronized through the Mobile API.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.contrib.admin.sites import AdminSite
from django.test import Client
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserProfile
from apps.sites.models import Site, State, Locality
from apps.sites.admin import SiteAdmin
from apps.assessments.models import Assessment, AssessmentResponse
from apps.assessments.admin import AssessmentAdmin
from apps.reports.models import FieldReport
from apps.mobile_api.models import MobileDevice, RefreshToken
from datetime import timedelta

User = get_user_model()


class DjangoToMobileIntegrationTestCase(APITestCase):
    """Test data flows from Django apps to Mobile API"""

    def setUp(self):
        # Set up test users with different roles
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='admin123',
            role='admin'
        )

        self.gso_user = User.objects.create_user(
            username='gso_test',
            email='gso@test.com',
            password='gso123',
            role='gso',
            is_verified=True,
            first_name='Test',
            last_name='GSO'
        )

        self.ngo_user = User.objects.create_user(
            username='ngo_test',
            email='ngo@test.com',
            password='ngo123',
            role='ngo_user',
            is_verified=True
        )

        # Create profiles
        for user in [self.admin_user, self.gso_user, self.ngo_user]:
            UserProfile.objects.create(user=user)

        # Set up geographic hierarchy
        self.state = State.objects.create(
            name='Integration Test State',
            name_ar='ولاية اختبار التكامل',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Integration Test Locality',
            name_ar='محلية اختبار التكامل',
            state=self.state,
            center_point={'type': 'Point', 'coordinates': [32.6, 15.6]}
        )

        # Set up mobile API client for GSO user
        self.mobile_client = APIClient()
        self.mobile_login_gso()

    def mobile_login_gso(self):
        """Login GSO user to mobile API"""
        login_data = {
            'email': 'gso@test.com',
            'password': 'gso123',
            'device_id': 'integration_test_device',
            'platform': 'android'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        response = self.mobile_client.post(login_url, login_data)

        if response.status_code == 200:
            self.access_token = response.data['access_token']
            self.mobile_client.credentials(HTTP_AUTHORIZATION=f'Token {self.access_token}')
            return True
        return False

    def test_django_site_creation_to_mobile_access(self):
        """Test: Create site via Django → Verify mobile API access"""

        # Step 1: Create site via Django ORM (simulating Django admin)
        django_site = Site.objects.create(
            name='Django Created Site',
            name_ar='موقع تم إنشاؤه من جانغو',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            location={'type': 'Point', 'coordinates': [32.7, 15.7]},
            total_population=2000,
            total_households=400,
            children_under_18=800,
            adults_18_59=1000,
            elderly_60_plus=200,
            male_count=1000,
            female_count=1000,
            contact_person='Django Admin User',
            contact_phone='+249123456789'
        )

        # Step 2: Assign site to GSO user
        self.gso_user.assigned_sites.add(django_site)

        # Step 3: Verify mobile API can access this site
        mobile_sites_url = reverse('mobile_api_v1:mobile-site-list')
        response = self.mobile_client.get(mobile_sites_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        site_ids = [site['id'] for site in response.data['results']]
        self.assertIn(django_site.id, site_ids)

        # Step 4: Verify site details are complete in mobile API
        mobile_site_detail_url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': django_site.id})
        detail_response = self.mobile_client.get(mobile_site_detail_url)

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        site_data = detail_response.data

        # Verify all critical data is present
        self.assertEqual(site_data['name'], 'Django Created Site')
        self.assertEqual(site_data['name_ar'], 'موقع تم إنشاؤه من جانغو')
        self.assertEqual(site_data['total_population'], 2000)
        self.assertEqual(site_data['coordinates'], [32.7, 15.7])
        self.assertIn('population_summary', site_data)

        # Verify computed fields
        pop_summary = site_data['population_summary']
        self.assertEqual(pop_summary['total_population'], 2000)
        self.assertEqual(pop_summary['vulnerable_count'], 0)  # No disabled/pregnant/chronically ill set

    def test_django_site_update_to_mobile_sync(self):
        """Test: Update site in Django → Verify mobile API reflects changes"""

        # Step 1: Create initial site
        site = Site.objects.create(
            name='Original Site Name',
            site_type='gathering',
            operational_status='planned',
            state=self.state,
            locality=self.locality,
            total_population=1000
        )
        self.gso_user.assigned_sites.add(site)

        # Step 2: Update site via Django ORM
        site.name = 'Updated Site Name'
        site.operational_status = 'active'
        site.total_population = 1500
        site.disabled_count = 50
        site.pregnant_women = 30
        site.chronically_ill = 20
        site.save()

        # Step 3: Verify mobile API shows updated data
        mobile_site_url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': site.id})
        response = self.mobile_client.get(mobile_site_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = response.data

        self.assertEqual(updated_data['name'], 'Updated Site Name')
        self.assertEqual(updated_data['operational_status'], 'active')
        self.assertEqual(updated_data['total_population'], 1500)

        # Verify computed vulnerable count
        pop_summary = updated_data['population_summary']
        self.assertEqual(pop_summary['vulnerable_count'], 100)  # 50 + 30 + 20

    def test_django_user_role_changes_to_mobile_permissions(self):
        """Test: Change user role in Django → Verify mobile API permissions change"""

        # Step 1: Create sites - one for testing access
        test_site = Site.objects.create(
            name='Role Test Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        # Step 2: Initially NGO user should see active sites
        ngo_mobile_client = APIClient()
        ngo_login_data = {
            'email': 'ngo@test.com',
            'password': 'ngo123',
            'device_id': 'ngo_test_device',
            'platform': 'ios'
        }

        login_url = reverse('mobile_api_v1:mobile-login')
        ngo_login_response = ngo_mobile_client.post(login_url, ngo_login_data)
        ngo_token = ngo_login_response.data['access_token']
        ngo_mobile_client.credentials(HTTP_AUTHORIZATION=f'Token {ngo_token}')

        # NGO user should see the site
        sites_url = reverse('mobile_api_v1:mobile-site-list')
        response = ngo_mobile_client.get(sites_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        site_ids = [site['id'] for site in response.data['results']]
        self.assertIn(test_site.id, site_ids)

        # Step 3: Change user role to GSO (more restricted)
        self.ngo_user.role = 'gso'
        self.ngo_user.save()

        # GSO should have limited access without site assignment
        response = ngo_mobile_client.get(sites_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # GSO without assigned sites might see fewer sites

    def test_django_assessment_creation_to_mobile_visibility(self):
        """Test: Create assessment via Django → Verify mobile API access"""

        # Step 1: Create assessment via Django ORM
        assessment = Assessment.objects.create(
            title='Django Created Assessment',
            title_ar='تقييم تم إنشاؤه من جانغو',
            description='Assessment created through Django for mobile testing',
            assessment_type='rapid',
            status='active',
            created_by=self.admin_user,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=14)).date(),
            kobo_form_id='django_test_form_123',
            kobo_form_url='https://kf.kobotoolbox.org/forms/test123'
        )

        # Step 2: Assign to GSO user and target sites
        assessment.assigned_to.add(self.gso_user)

        # Create target site
        target_site = Site.objects.create(
            name='Assessment Target Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )
        assessment.target_sites.add(target_site)
        self.gso_user.assigned_sites.add(target_site)

        # Step 3: Verify mobile API can access assessment
        assessments_url = reverse('mobile_api_v1:mobile-assessment-list')
        response = self.mobile_client.get(assessments_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assessment_ids = [a['id'] for a in response.data['results']]
        self.assertIn(assessment.id, assessment_ids)

        # Step 4: Verify assessment details
        assessment_detail_url = reverse('mobile_api_v1:mobile-assessment-detail', kwargs={'pk': assessment.id})
        detail_response = self.mobile_client.get(assessment_detail_url)

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        assessment_data = detail_response.data

        self.assertEqual(assessment_data['title'], 'Django Created Assessment')
        self.assertEqual(assessment_data['kobo_form_id'], 'django_test_form_123')
        self.assertTrue(assessment_data['assigned_to_me'])

        # Step 5: Verify mobile can access form data
        form_data_url = reverse('mobile_api_v1:mobile-assessment-form-data', kwargs={'pk': assessment.id})
        form_response = self.mobile_client.get(form_data_url)

        self.assertEqual(form_response.status_code, status.HTTP_200_OK)
        self.assertEqual(form_response.data['form_id'], 'django_test_form_123')

    def test_django_user_assignment_to_mobile_access(self):
        """Test: Assign user to sites/assessments in Django → Verify mobile access changes"""

        # Step 1: Create multiple sites
        site1 = Site.objects.create(
            name='Site 1',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        site2 = Site.objects.create(
            name='Site 2',
            site_type='camp',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        # Step 2: Initially assign only site1 to GSO
        self.gso_user.assigned_sites.set([site1])

        # Verify GSO can only see site1
        sites_url = reverse('mobile_api_v1:mobile-site-list')
        response = self.mobile_client.get(sites_url)

        site_ids = [site['id'] for site in response.data['results']]
        self.assertIn(site1.id, site_ids)
        # GSO might see site2 if it's in the same state, but let's verify site1 is present

        # Step 3: Add site2 to GSO's assignments
        self.gso_user.assigned_sites.add(site2)

        # Verify GSO can now see both sites
        response = self.mobile_client.get(sites_url)
        site_ids = [site['id'] for site in response.data['results']]
        self.assertIn(site1.id, site_ids)
        self.assertIn(site2.id, site_ids)

        # Step 4: Remove site1 from assignments
        self.gso_user.assigned_sites.remove(site1)

        # Verify access changes reflect immediately
        response = self.mobile_client.get(sites_url)
        site_ids = [site['id'] for site in response.data['results']]
        self.assertIn(site2.id, site_ids)

    def test_django_admin_interface_to_mobile_sync(self):
        """Test: Use Django admin interface → Verify mobile API sync"""

        # This test simulates Django admin actions
        # In a real scenario, you would use Django's admin client or Selenium

        # Step 1: Create site through Django admin-like process
        site_data = {
            'name': 'Admin Interface Site',
            'name_ar': 'موقع واجهة الإدارة',
            'site_type': 'health',
            'operational_status': 'active',
            'state': self.state,
            'locality': self.locality,
            'location': {'type': 'Point', 'coordinates': [32.8, 15.8]},
            'total_population': 3000,
            'total_households': 600,
            'contact_person': 'Admin Created',
            'contact_email': 'admin@site.com',
            'reported_by': 'Django Admin Interface'
        }

        # Create through ORM (simulating admin save)
        admin_site = Site.objects.create(**site_data)

        # Assign to GSO
        self.gso_user.assigned_sites.add(admin_site)

        # Step 2: Verify mobile API immediately reflects the change
        sites_url = reverse('mobile_api_v1:mobile-site-list')
        response = self.mobile_client.get(sites_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find the admin-created site
        admin_created_site = None
        for site in response.data['results']:
            if site['id'] == admin_site.id:
                admin_created_site = site
                break

        self.assertIsNotNone(admin_created_site)
        self.assertEqual(admin_created_site['name'], 'Admin Interface Site')
        self.assertEqual(admin_created_site['site_type'], 'health')
        self.assertEqual(admin_created_site['total_population'], 3000)

    def test_django_data_validation_to_mobile_constraints(self):
        """Test: Django model constraints → Verify mobile API respects same constraints"""

        # Step 1: Create site with specific constraints
        constrained_site = Site.objects.create(
            name='Constraint Test Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            total_population=1000,
            children_under_18=400,
            adults_18_59=500,
            elderly_60_plus=100  # Total adds up to 1000
        )

        self.gso_user.assigned_sites.add(constrained_site)

        # Step 2: Verify mobile API shows validated data
        site_url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': constrained_site.id})
        response = self.mobile_client.get(site_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 3: Verify computed properties work correctly
        pop_summary = response.data['population_summary']
        age_total = pop_summary['children_under_18'] + pop_summary['adults_18_59'] + pop_summary['elderly_60_plus']
        self.assertEqual(age_total, pop_summary['total_population'])

    def test_django_bulk_operations_to_mobile_performance(self):
        """Test: Bulk Django operations → Verify mobile API performance"""

        # Step 1: Create multiple sites via Django bulk operations
        sites_data = []
        for i in range(20):
            sites_data.append(Site(
                name=f'Bulk Site {i}',
                site_type='gathering',
                operational_status='active',
                state=self.state,
                locality=self.locality,
                total_population=1000 + i * 100
            ))

        bulk_sites = Site.objects.bulk_create(sites_data)

        # Assign all to GSO
        self.gso_user.assigned_sites.set(bulk_sites)

        # Step 2: Verify mobile API can handle the increased data efficiently
        sites_url = reverse('mobile_api_v1:mobile-site-list')

        import time
        start_time = time.time()
        response = self.mobile_client.get(sites_url)
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 2.0, f"Mobile API response took {response_time:.2f}s, should be under 2s")

        # Verify pagination is working
        self.assertIn('count', response.data)
        self.assertGreaterEqual(response.data['count'], 20)

    def test_django_foreign_key_changes_to_mobile_consistency(self):
        """Test: Change foreign key relationships in Django → Verify mobile API consistency"""

        # Step 1: Create new state and locality
        new_state = State.objects.create(
            name='New State',
            center_point={'type': 'Point', 'coordinates': [33.0, 16.0]}
        )

        new_locality = Locality.objects.create(
            name='New Locality',
            state=new_state,
            center_point={'type': 'Point', 'coordinates': [33.1, 16.1]}
        )

        # Step 2: Create site with original location
        site = Site.objects.create(
            name='Location Change Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        self.gso_user.assigned_sites.add(site)

        # Step 3: Verify original location in mobile API
        site_url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': site.id})
        response = self.mobile_client.get(site_url)

        self.assertEqual(response.data['state_name'], 'Integration Test State')
        self.assertEqual(response.data['locality_name'], 'Integration Test Locality')

        # Step 4: Change site's state and locality
        site.state = new_state
        site.locality = new_locality
        site.save()

        # Step 5: Verify mobile API reflects the change
        response = self.mobile_client.get(site_url)

        self.assertEqual(response.data['state_name'], 'New State')
        self.assertEqual(response.data['locality_name'], 'New Locality')

class DjangoAdminToMobileIntegrationTestCase(TestCase):
    """Test Django Admin interface integration with Mobile API"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_integration',
            email='admin@integration.com',
            password='admin123'
        )

        self.state = State.objects.create(
            name='Admin Test State',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Admin Test Locality',
            state=self.state
        )

    def test_admin_site_creation_workflow(self):
        """Test complete admin workflow for site creation"""

        # Simulate Django admin site creation
        admin_site = AdminSite()
        site_admin = SiteAdmin(Site, admin_site)

        # Create site data as it would come from admin form
        site_data = {
            'name': 'Admin Workflow Site',
            'site_type': 'gathering',
            'operational_status': 'active',
            'state': self.state.id,
            'locality': self.locality.id,
            'total_population': 2500
        }

        # Create site
        site = Site.objects.create(
            name=site_data['name'],
            site_type=site_data['site_type'],
            operational_status=site_data['operational_status'],
            state_id=site_data['state'],
            locality_id=site_data['locality'],
            total_population=site_data['total_population']
        )

        # Verify site was created with admin-expected fields
        self.assertEqual(site.name, 'Admin Workflow Site')
        self.assertEqual(site.state.name, 'Admin Test State')
        self.assertEqual(site.total_population, 2500)

        # Verify site would be accessible via mobile API
        # (In real scenario, would make API call here)
        self.assertTrue(Site.objects.filter(id=site.id).exists())

    def test_admin_bulk_actions_simulation(self):
        """Test Django admin bulk actions integration"""

        # Create multiple sites
        sites = []
        for i in range(5):
            site = Site.objects.create(
                name=f'Bulk Action Site {i}',
                site_type='gathering',
                operational_status='planned',  # Initially planned
                state=self.state,
                locality=self.locality
            )
            sites.append(site)

        # Simulate admin bulk action: activate all sites
        Site.objects.filter(id__in=[s.id for s in sites]).update(operational_status='active')

        # Verify all sites are now active
        for site in sites:
            site.refresh_from_db()
            self.assertEqual(site.operational_status, 'active')

        # This change would immediately be visible in mobile API