from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from apps.accounts.models import UserProfile
from apps.mobile_api.models import MobileDevice, RefreshToken

User = get_user_model()


class MobileAuthenticationTestCase(APITestCase):
    """Test mobile authentication endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'organization': 'Test Org',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'device_id': 'test_device_123',
            'platform': 'android',
            'fcm_token': 'test_fcm_token'
        }

        self.login_data = {
            'email': 'testuser@example.com',
            'password': 'testpass123',
            'device_id': 'test_device_123',
            'platform': 'android'
        }

    def test_mobile_register_success(self):
        """Test successful mobile registration"""
        url = reverse('mobile_api_v1:mobile-register')
        response = self.client.post(url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user_id', response.data)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_mobile_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email=self.user_data['email'],
            password='password123'
        )

        url = reverse('mobile_api_v1:mobile-register')
        response = self.client.post(url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_register_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.user_data.copy()
        data['password_confirm'] = 'different_password'

        url = reverse('mobile_api_v1:mobile-register')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_login_success(self):
        """Test successful mobile login"""
        # Create verified user
        user = User.objects.create_user(
            username='testuser',
            email=self.login_data['email'],
            password=self.login_data['password'],
            is_verified=True
        )
        UserProfile.objects.create(user=user)

        url = reverse('mobile_api_v1:mobile-login')
        response = self.client.post(url, self.login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertIn('device_id', response.data)

        # Check if device was created
        self.assertTrue(MobileDevice.objects.filter(device_id='test_device_123').exists())

    def test_mobile_login_unverified_user(self):
        """Test login with unverified user"""
        User.objects.create_user(
            username='testuser',
            email=self.login_data['email'],
            password=self.login_data['password'],
            is_verified=False
        )

        url = reverse('mobile_api_v1:mobile-login')
        response = self.client.post(url, self.login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('mobile_api_v1:mobile-login')
        response = self.client.post(url, self.login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_success(self):
        """Test successful token refresh"""
        # Create user and device
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            is_verified=True
        )

        device = MobileDevice.objects.create(
            user=user,
            device_id='test_device',
            platform='android'
        )

        refresh_token = RefreshToken.objects.create(
            user=user,
            device=device,
            token='test_refresh_token',
            expires_at=timezone.now() + timedelta(days=30)
        )

        url = reverse('mobile_api_v1:refresh-token')
        response = self.client.post(url, {'refresh_token': refresh_token.token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)

        # Check if old refresh token is revoked
        refresh_token.refresh_from_db()
        self.assertTrue(refresh_token.is_revoked)

    def test_refresh_token_expired(self):
        """Test refresh with expired token"""
        from django.utils import timezone
        from datetime import timedelta

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        device = MobileDevice.objects.create(
            user=user,
            device_id='test_device',
            platform='android'
        )

        # Create expired refresh token
        refresh_token = RefreshToken.objects.create(
            user=user,
            device=device,
            token='expired_token',
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )

        url = reverse('mobile_api_v1:refresh-token')
        response = self.client.post(url, {'refresh_token': refresh_token.token})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mobile_logout_success(self):
        """Test successful mobile logout"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        token = Token.objects.create(user=user)
        self.client.force_authenticate(user=user, token=token)

        url = reverse('mobile_api_v1:mobile-logout')
        response = self.client.post(url, {'device_id': 'test_device'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if token is deleted
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_mobile_profile_get(self):
        """Test getting mobile user profile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='password123'
        )
        UserProfile.objects.create(user=user)

        self.client.force_authenticate(user=user)

        url = reverse('mobile_api_v1:mobile-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)
        self.assertEqual(response.data['full_name'], 'Test User')

    def test_mobile_profile_update(self):
        """Test updating mobile user profile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        UserProfile.objects.create(user=user)

        self.client.force_authenticate(user=user)

        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+1234567890'
        }

        url = reverse('mobile_api_v1:mobile-profile')
        response = self.client.patch(url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.phone_number, '+1234567890')


class DeviceManagementTestCase(APITestCase):
    """Test mobile device management"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.user)

        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='test_device_123',
            platform='android',
            fcm_token='test_fcm_token'
        )

    def test_list_user_devices(self):
        """Test listing user's devices"""
        url = reverse('mobile_api_v1:device-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['device_id'], 'test_device_123')

    def test_update_fcm_token(self):
        """Test updating FCM token"""
        url = reverse('mobile_api_v1:device-update-fcm-token', kwargs={'pk': self.device.id})
        response = self.client.post(url, {'fcm_token': 'new_fcm_token'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.device.refresh_from_db()
        self.assertEqual(self.device.fcm_token, 'new_fcm_token')

    def test_update_fcm_token_missing(self):
        """Test updating FCM token without providing token"""
        url = reverse('mobile_api_v1:device-update-fcm-token', kwargs={'pk': self.device.id})
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)