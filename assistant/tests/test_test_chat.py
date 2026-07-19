from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from assistant.models import Contact, Message


class TestChatViewTests(TestCase):
    def test_get_test_chat_creates_local_conversation(self):
        response = self.client.get(reverse('test-chat'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Local Test Chat')
        self.assertTrue(Contact.objects.filter(phone_number='local-test-chat').exists())

    @patch('assistant.services.whatsapp.WhatsAppClient.send_text')
    def test_post_test_chat_saves_messages_without_whatsapp_api(self, send_text):
        response = self.client.post(reverse('test-chat'), {'message': 'Hello assistant'})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(send_text.called)
        messages = Message.objects.order_by('created_at')
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].text, 'Hello assistant')
        self.assertEqual(messages[0].sender_type, Message.SenderType.CONTACT)
        self.assertEqual(messages[1].text, "I am currently unavailable, so my AI assistant is replying for me.")
        self.assertEqual(messages[1].sender_type, Message.SenderType.AI)
        self.assertEqual(messages[1].raw_payload, {'source': 'local_test_chat'})

    @patch('assistant.services.whatsapp.WhatsAppClient.send_text')
    def test_post_test_chat_applies_safety_rules_without_reply(self, send_text):
        response = self.client.post(reverse('test-chat'), {'message': 'Please send me the OTP'}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'otp or password')
        self.assertFalse(send_text.called)
        self.assertEqual(Message.objects.count(), 1)
        conversation = Message.objects.get().conversation
        self.assertTrue(conversation.escalated)
        self.assertEqual(conversation.escalation_reason, 'otp or password')
