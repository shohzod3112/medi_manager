# core/tests.py
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="testuser", password="password123")
    
    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {"username": "testuser", "password": "password123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_failure_invalid_credentials(self):
        response = self.client.post('/api/auth/login/', {"username": "wronguser", "password": "wrongpass"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
