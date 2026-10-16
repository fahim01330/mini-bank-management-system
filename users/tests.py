from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-register')
        self.login_url = reverse('user-login')
        self.profile_url = reverse('user-profile')

        self.user_data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "first_name": "Alice",
            "last_name": "Smith",
            "phone_number": "+1234567890",
            "address": "123 Main St",
        }

    def test_customer_registration_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'alice')
        self.assertTrue(User.objects.filter(username='alice').exists())

    def test_customer_registration_mismatched_password(self):
        data = self.user_data.copy()
        data['password_confirm'] = "DifferentPass123!"
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_login_success(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {
            "username": "alice",
            "password": "Password123!"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

    def test_customer_login_invalid_credentials(self):
        login_data = {
            "username": "alice",
            "password": "WrongPassword!"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_and_update_own_profile(self):
        reg_response = self.client.post(self.register_url, self.user_data, format='json')
        token = reg_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # View profile
        get_response = self.client.get(self.profile_url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['email'], 'alice@example.com')

        # Update profile
        patch_response = self.client.patch(self.profile_url, {"phone_number": "+9876543210"}, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data['phone_number'], "+9876543210")

    def test_profile_unauthenticated_access_denied(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
