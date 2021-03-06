from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='test@admin.com',
            password='Pest1235'
        )

        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='test@user.com',
            password='Pest5321',
            name='Full user name'
        )

    def test_user_listed(self):
        url = reverse('admin:core_user_changelist')
        result = self.client.get(url)

        self.assertContains(result, self.user.email)
        self.assertContains(result, self.user.name)

    def test_change_user_page(self):
        url = reverse('admin:core_user_change', args=[self.user.id])
        result = self.client.get(url)

        self.assertEqual(result.status_code, 200)

    def test_create_user_page(self):
        url = reverse('admin:core_user_add')
        result = self.client.get(url)

        self.assertEqual(result.status_code, 200)
