from django.test import TestCase
from django.urls import reverse


class PublicPageTests(TestCase):
    def test_privacy_policy_is_public(self):
        response = self.client.get(reverse('privacy-policy'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Privacy Policy')
        self.assertContains(response, 'Bilal AI Assistant')
        self.assertContains(response, 'WhatsApp messages and phone numbers may be processed only')
        self.assertContains(response, 'does not sell')
        self.assertContains(response, 'bilalshafqat35@gmail.com')

    def test_data_deletion_is_public(self):
        response = self.client.get(reverse('data-deletion'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Deletion')
        self.assertContains(response, 'Bilal AI Assistant')
        self.assertContains(response, 'WhatsApp messages and phone numbers may be processed only')
        self.assertContains(response, 'does not sell user data')
        self.assertContains(response, 'bilalshafqat35@gmail.com')
