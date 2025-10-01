from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.sites.models import Site, State, Locality
from apps.mobile_api.models import MobileDevice

User = get_user_model()


class MobileSitesTestCase(APITestCase):
    """Test mobile sites API endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.gso_user = User.objects.create_user(
            username='gso_user',
            email='gso@example.com',
            password='password123',
            role='gso',
            is_verified=True
        )

        self.ngo_user = User.objects.create_user(
            username='ngo_user',
            email='ngo@example.com',
            password='password123',
            role='ngo_user',
            is_verified=True
        )

        # Create geographic entities
        self.state = State.objects.create(
            name='Test State',
            name_ar='ولاية اختبار',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Test Locality',
            name_ar='محلية اختبار',
            state=self.state,
            center_point={'type': 'Point', 'coordinates': [32.6, 15.6]}
        )

        # Create test sites
        self.site1 = Site.objects.create(
            name='Test Gathering Site 1',
            name_ar='موقع تجمع تجريبي 1',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            location={'type': 'Point', 'coordinates': [32.7, 15.7]},
            total_population=1000,
            total_households=200
        )

        self.site2 = Site.objects.create(
            name='Test Camp Site 2',
            name_ar='مخيم تجريبي 2',
            site_type='camp',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            location={'type': 'Point', 'coordinates': [32.8, 15.8]},
            total_population=1500,
            total_households=300
        )

        # Assign site to GSO user
        self.gso_user.assigned_sites.add(self.site1)

    def test_list_sites_as_gso(self):
        """Test listing sites as GSO user (should see assigned sites)"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # GSO should see assigned sites and sites in their state
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_list_sites_as_ngo(self):
        """Test listing sites as NGO user (should see active sites)"""
        self.client.force_authenticate(user=self.ngo_user)

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # NGO user should see active sites
        self.assertEqual(len(response.data['results']), 2)

    def test_site_detail(self):
        """Test getting site details"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': self.site1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Gathering Site 1')
        self.assertEqual(response.data['site_type'], 'gathering')
        self.assertIn('population_summary', response.data)
        self.assertIn('coordinates', response.data)

    def test_create_site_as_gso(self):
        """Test creating a new site as GSO user"""
        self.client.force_authenticate(user=self.gso_user)

        site_data = {
            'name': 'New Test Site',
            'name_ar': 'موقع جديد للاختبار',
            'site_type': 'gathering',
            'operational_status': 'active',
            'state': self.state.id,
            'locality': self.locality.id,
            'location': {'type': 'Point', 'coordinates': [32.9, 15.9]},
            'total_population': 800,
            'total_households': 160,
            'contact_person': 'Test Contact',
            'contact_phone': '+249123456789'
        }

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.post(url, site_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.filter(name='New Test Site').count(), 1)

    def test_create_site_invalid_location(self):
        """Test creating site with invalid location format"""
        self.client.force_authenticate(user=self.gso_user)

        site_data = {
            'name': 'Invalid Location Site',
            'site_type': 'gathering',
            'location': {'type': 'Point', 'coordinates': [200, 100]}  # Invalid coordinates
        }

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.post(url, site_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_site(self):
        """Test updating site information"""
        self.client.force_authenticate(user=self.gso_user)

        update_data = {
            'total_population': 1200,
            'total_households': 240,
            'contact_person': 'Updated Contact'
        }

        url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': self.site1.id})
        response = self.client.patch(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.site1.refresh_from_db()
        self.assertEqual(self.site1.total_population, 1200)
        self.assertEqual(self.site1.contact_person, 'Updated Contact')

    def test_nearby_sites(self):
        """Test getting nearby sites"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-site-nearby')
        response = self.client.get(url, {
            'lat': 15.7,
            'lon': 32.7,
            'radius': 50  # 50km radius
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_nearby_sites_missing_coordinates(self):
        """Test nearby sites without providing coordinates"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-site-nearby')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sites_summary(self):
        """Test getting sites summary statistics"""
        self.client.force_authenticate(user=self.ngo_user)

        url = reverse('mobile_api_v1:mobile-site-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sites', response.data)
        self.assertIn('active_sites', response.data)
        self.assertIn('total_population', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('by_status', response.data)

    def test_filter_sites_by_type(self):
        """Test filtering sites by type"""
        self.client.force_authenticate(user=self.ngo_user)

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url, {'site_type': 'gathering'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only gathering sites
        for site in response.data['results']:
            self.assertEqual(site['site_type'], 'gathering')

    def test_search_sites(self):
        """Test searching sites by name"""
        self.client.force_authenticate(user=self.ngo_user)

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url, {'search': 'Gathering'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return sites matching search term
        self.assertGreater(len(response.data['results']), 0)

    def test_order_sites(self):
        """Test ordering sites"""
        self.client.force_authenticate(user=self.ngo_user)

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url, {'ordering': '-total_population'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        if len(results) > 1:
            # Should be ordered by population descending
            self.assertGreaterEqual(
                results[0]['total_population'] or 0,
                results[1]['total_population'] or 0
            )

    def test_unauthorized_access(self):
        """Test accessing sites without authentication"""
        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_site_pagination(self):
        """Test sites pagination"""
        # Create more sites for pagination test
        for i in range(25):
            Site.objects.create(
                name=f'Pagination Site {i}',
                site_type='gathering',
                operational_status='active',
                state=self.state,
                locality=self.locality
            )

        self.client.force_authenticate(user=self.ngo_user)

        url = reverse('mobile_api_v1:mobile-site-list')
        response = self.client.get(url, {'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertLessEqual(len(response.data['results']), 10)

    def test_site_serialization_fields(self):
        """Test that site serialization includes all required fields"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': self.site1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        required_fields = [
            'id', 'name', 'name_ar', 'site_type', 'operational_status',
            'state_name', 'locality_name', 'coordinates', 'population_summary',
            'last_updated'
        ]

        for field in required_fields:
            self.assertIn(field, response.data, f"Field {field} missing from response")

    def test_population_summary_calculation(self):
        """Test that population summary is calculated correctly"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-site-detail', kwargs={'pk': self.site1.id})
        response = self.client.get(url)

        population_summary = response.data['population_summary']
        self.assertEqual(population_summary['total_population'], 1000)
        self.assertEqual(population_summary['total_households'], 200)