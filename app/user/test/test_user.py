from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (Public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload successfully"""
        payload = {
            'name': 'Carlos Test',
            'email': 'test@email.test',
            'password': 'testpass'
        }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
         payload = {
             'name': 'Carlos Test',
             'email': 'test@email.test',
             'password': 'testpass'
         }

         create_user(**payload)

         response = self.client.post(CREATE_USER_URL, payload)

         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
             'name': 'Carlos Test',
             'email': 'test@email.test',
             'password': 'te'
        }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email = payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        payload = {'email': 'carlospaniagua83@gmail.com', 'password': 'testpass123'}
        create_user(**payload)

        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_create_token_invalid_credentials(self):
        payload = {'email': 'carlospaniagua84@gmail.com', 'password': 'testpass'}
        create_user(**payload)
        response = self.client.post(TOKEN_URL, {
            'email': 'carlospaniagua84@gmail.com', 'password': 'testpass1234'
        })

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        response = self.client.post(TOKEN_URL, {
            'email': 'carlospaniagua85@gmail.com', 'password': 'testpass1234'
        })

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        response = self.client.post(TOKEN_URL, {
            'email': 'carlospaniagua85@gmail.com', 'password': ''
        })

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
