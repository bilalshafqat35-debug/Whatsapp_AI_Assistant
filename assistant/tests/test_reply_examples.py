from unittest.mock import Mock, patch

from django.contrib import admin
from django.test import TestCase

from assistant.models import AssistantSettings, Contact, ReplyExample
from assistant.services.instructions import build_ai_instructions
from assistant.services.processor import process_inbound_text
from assistant.services.reply_examples import relevant_reply_examples


class ReplyExampleTests(TestCase):
    def test_reply_example_registered_in_admin(self):
        self.assertIn(ReplyExample, admin.site._registry)

    def test_build_ai_instructions_includes_most_relevant_active_examples_and_safety(self):
        settings = AssistantSettings.singleton()
        ReplyExample.objects.create(
            incoming_message='Are you free for chai tonight?',
            bilal_reply='Haan bro chai ka scene kar lete hain, bas time bata do.',
        )
        ReplyExample.objects.create(
            incoming_message='Can you share the OTP?',
            bilal_reply='Nahi yaar OTP share nahi kar sakta.',
            is_active=False,
        )
        ReplyExample.objects.create(
            incoming_message='Please send the project update',
            bilal_reply='Bilkul, thori dair mein update bhej deta hoon.',
        )

        instructions = build_ai_instructions(settings, latest_message='chai ka plan tonight?')

        self.assertIn('Never answer sensitive, urgent, financial, OTP, password, or highly personal requests', instructions)
        self.assertIn('Reply examples for Bilal style', instructions)
        self.assertIn('Haan bro chai ka scene kar lete hain', instructions)
        self.assertIn('Bilkul, thori dair mein update bhej deta hoon', instructions)
        self.assertNotIn('OTP share nahi kar sakta', instructions)

    def test_relevant_reply_examples_orders_by_message_overlap(self):
        project = ReplyExample.objects.create(
            incoming_message='Please send the project update today',
            bilal_reply='Project update bhej deta hoon.',
        )
        ReplyExample.objects.create(
            incoming_message='Coffee tomorrow?',
            bilal_reply='Kal dekhte hain.',
        )

        examples = relevant_reply_examples('Any project update?', limit=1)

        self.assertEqual(examples, [project])

    @patch('assistant.services.processor.WhatsAppClient')
    @patch('assistant.services.processor.get_ai_service')
    def test_processor_passes_reply_examples_to_ai_without_breaking_history(self, get_ai_service, whatsapp_client):
        ReplyExample.objects.create(
            incoming_message='Any project update?',
            bilal_reply='Haan yaar, project update thori dair mein bhejta hoon.',
        )
        ai_service = Mock()
        ai_service.generate_reply.return_value = 'Test reply'
        get_ai_service.return_value = ai_service

        result = process_inbound_text(phone_number='15551234567', text='Project update?', whatsapp_message_id='wamid.1')

        self.assertEqual(result, {'status': 'replied'})
        ai_service.generate_reply.assert_called_once()
        kwargs = ai_service.generate_reply.call_args.kwargs
        self.assertIn('Haan yaar, project update', kwargs['instructions'])
        self.assertEqual(kwargs['latest_message'], 'Project update?')
        self.assertIsInstance(kwargs['contact'], Contact)
        self.assertEqual(kwargs['history'], [])
        whatsapp_client.return_value.send_text.assert_called_once_with('15551234567', 'Test reply')
