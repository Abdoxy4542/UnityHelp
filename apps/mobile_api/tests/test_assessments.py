from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.sites.models import Site, State, Locality
from apps.assessments.models import Assessment, AssessmentResponse
from datetime import timedelta

User = get_user_model()


class MobileAssessmentsTestCase(APITestCase):
    """Test mobile assessments API endpoints"""

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

        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='password123',
            role='admin',
            is_verified=True
        )

        # Create geographic entities
        self.state = State.objects.create(
            name='Test State',
            center_point={'type': 'Point', 'coordinates': [32.5, 15.5]}
        )

        self.locality = Locality.objects.create(
            name='Test Locality',
            state=self.state,
            center_point={'type': 'Point', 'coordinates': [32.6, 15.6]}
        )

        # Create test site
        self.site = Site.objects.create(
            name='Test Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality,
            location={'type': 'Point', 'coordinates': [32.7, 15.7]}
        )

        # Create test assessments
        self.assessment1 = Assessment.objects.create(
            title='Rapid Needs Assessment',
            title_ar='تقييم سريع للاحتياجات',
            description='Quick assessment of basic needs',
            assessment_type='rapid',
            status='active',
            created_by=self.admin_user,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=7)).date(),
            kobo_form_id='test_form_123',
            kobo_form_url='https://kf.kobotoolbox.org/test_form'
        )

        self.assessment2 = Assessment.objects.create(
            title='Detailed Site Assessment',
            assessment_type='detailed',
            status='draft',
            created_by=self.admin_user
        )

        # Assign assessment to user and site
        self.assessment1.assigned_to.add(self.gso_user)
        self.assessment1.target_sites.add(self.site)

    def test_list_assessments_as_gso(self):
        """Test listing assessments as GSO user"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see at least the assigned assessment
        self.assertGreater(len(response.data['results']), 0)

        # Check if assessment data includes required fields
        assessment_data = response.data['results'][0]
        required_fields = [
            'id', 'title', 'assessment_type', 'status',
            'created_by_name', 'assigned_to_me', 'response_count'
        ]
        for field in required_fields:
            self.assertIn(field, assessment_data)

    def test_get_my_assignments(self):
        """Test getting assessments assigned to current user"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-my-assignments')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.assessment1.id)

    def test_assessment_detail(self):
        """Test getting assessment details"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-detail', kwargs={'pk': self.assessment1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Rapid Needs Assessment')
        self.assertEqual(response.data['kobo_form_id'], 'test_form_123')

    def test_get_form_data(self):
        """Test getting Kobo form data for assessment"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-form-data', kwargs={'pk': self.assessment1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('form_id', response.data)
        self.assertIn('form_url', response.data)
        self.assertEqual(response.data['form_id'], 'test_form_123')

    def test_filter_assessments_by_type(self):
        """Test filtering assessments by type"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-list')
        response = self.client.get(url, {'assessment_type': 'rapid'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for assessment in response.data['results']:
            self.assertEqual(assessment['assessment_type'], 'rapid')

    def test_filter_assessments_by_status(self):
        """Test filtering assessments by status"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-list')
        response = self.client.get(url, {'status': 'active'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for assessment in response.data['results']:
            self.assertEqual(assessment['status'], 'active')

    def test_search_assessments(self):
        """Test searching assessments by title"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-list')
        response = self.client.get(url, {'search': 'Rapid'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_unauthorized_assessment_access(self):
        """Test accessing assessments without authentication"""
        url = reverse('mobile_api_v1:mobile-assessment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MobileAssessmentResponsesTestCase(APITestCase):
    """Test mobile assessment responses API endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create test user
        self.gso_user = User.objects.create_user(
            username='gso_user',
            email='gso@example.com',
            password='password123',
            role='gso',
            is_verified=True
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

        # Create test site
        self.site = Site.objects.create(
            name='Test Site',
            site_type='gathering',
            operational_status='active',
            state=self.state,
            locality=self.locality
        )

        # Create test assessment
        self.assessment = Assessment.objects.create(
            title='Test Assessment',
            assessment_type='rapid',
            status='active',
            created_by=self.gso_user
        )

        # Create test response
        self.response = AssessmentResponse.objects.create(
            assessment=self.assessment,
            site=self.site,
            respondent=self.gso_user,
            kobo_data={'question1': 'answer1', 'question2': 'answer2'},
            gps_location={'type': 'Point', 'coordinates': [32.7, 15.7]},
            is_submitted=False
        )

    def test_list_user_responses(self):
        """Test listing user's assessment responses"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.response.id)

    def test_create_assessment_response(self):
        """Test creating a new assessment response"""
        self.client.force_authenticate(user=self.gso_user)

        response_data = {
            'assessment': self.assessment.id,
            'site': self.site.id,
            'kobo_data': {'question1': 'new_answer1', 'question2': 'new_answer2'},
            'gps_location': {'type': 'Point', 'coordinates': [32.8, 15.8]}
        }

        url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response = self.client.post(url, response_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AssessmentResponse.objects.filter(respondent=self.gso_user).count(), 2)

    def test_update_assessment_response(self):
        """Test updating an assessment response"""
        self.client.force_authenticate(user=self.gso_user)

        update_data = {
            'kobo_data': {'question1': 'updated_answer1', 'question2': 'updated_answer2'}
        }

        url = reverse('mobile_api_v1:mobile-assessment-response-detail', kwargs={'pk': self.response.id})
        response = self.client.patch(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.response.refresh_from_db()
        self.assertEqual(self.response.kobo_data['question1'], 'updated_answer1')

    def test_submit_assessment_response(self):
        """Test submitting an assessment response"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-response-submit', kwargs={'pk': self.response.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.response.refresh_from_db()
        self.assertTrue(self.response.is_submitted)
        self.assertIsNotNone(self.response.submitted_at)

    def test_submit_already_submitted_response(self):
        """Test submitting an already submitted response"""
        self.client.force_authenticate(user=self.gso_user)

        # Mark response as submitted
        self.response.is_submitted = True
        self.response.submitted_at = timezone.now()
        self.response.save()

        url = reverse('mobile_api_v1:mobile-assessment-response-submit', kwargs={'pk': self.response.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_draft_responses(self):
        """Test getting draft (unsubmitted) responses"""
        self.client.force_authenticate(user=self.gso_user)

        # Create another draft response
        AssessmentResponse.objects.create(
            assessment=self.assessment,
            site=self.site,
            respondent=self.gso_user,
            kobo_data={'draft': 'data'},
            is_submitted=False
        )

        url = reverse('mobile_api_v1:mobile-assessment-response-drafts')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for draft in response.data:
            self.assertFalse(draft['is_submitted'])

    def test_filter_responses_by_assessment(self):
        """Test filtering responses by assessment"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response = self.client.get(url, {'assessment': self.assessment.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for resp in response.data['results']:
            self.assertEqual(resp['assessment'], self.assessment.id)

    def test_filter_responses_by_site(self):
        """Test filtering responses by site"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-response-list')
        response = self.client.get(url, {'site': self.site.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for resp in response.data['results']:
            self.assertEqual(resp['site'], self.site.id)

    def test_response_serialization_fields(self):
        """Test that response serialization includes all required fields"""
        self.client.force_authenticate(user=self.gso_user)

        url = reverse('mobile_api_v1:mobile-assessment-response-detail', kwargs={'pk': self.response.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        required_fields = [
            'id', 'assessment', 'assessment_title', 'site', 'site_name',
            'kobo_data', 'is_submitted', 'gps_location', 'created_at'
        ]

        for field in required_fields:
            self.assertIn(field, response.data, f"Field {field} missing from response")

    def test_cannot_access_other_users_responses(self):
        """Test that users cannot access other users' responses"""
        other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='password123',
            role='gso'
        )

        self.client.force_authenticate(user=other_user)

        url = reverse('mobile_api_v1:mobile-assessment-response-detail', kwargs={'pk': self.response.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)