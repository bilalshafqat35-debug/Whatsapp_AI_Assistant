from unittest.mock import Mock, patch

from django.contrib import admin
from django.test import TestCase, override_settings

from assistant.models import AssistantSettings, Contact, ReplyExample
from assistant.services.instructions import build_ai_instructions
from assistant.services.processor import process_inbound_text
from assistant.services.reply_examples import find_semantic_reply_example, relevant_reply_examples


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
        self.assertNotIn(settings.unavailable_message, instructions.split('\n\n')[0])

    def test_relevant_reply_examples_orders_by_multilingual_intent(self):
        where = ReplyExample.objects.create(
            incoming_message='kahan ho?',
            bilal_reply='Main office mein hoon.',
        )
        ReplyExample.objects.create(
            incoming_message='Coffee tomorrow?',
            bilal_reply='Kal dekhte hain.',
        )

        examples = relevant_reply_examples('kithe a?', limit=1)

        self.assertEqual(examples, [where])

    @override_settings(GEMINI_API_KEY='')
    def test_find_semantic_reply_example_matches_roman_urdu_punjabi_variations(self):
        where = ReplyExample.objects.create(
            incoming_message='kaha pe ho?',
            bilal_reply='Ghar pe hoon, thori dair mein nikalta hoon.',
        )

        self.assertEqual(find_semantic_reply_example('kidhar ho?'), where)
        self.assertEqual(find_semantic_reply_example('kithe a?'), where)

    @patch('assistant.services.processor.WhatsAppClient')
    @patch('assistant.services.processor.get_ai_service')
    @override_settings(GEMINI_API_KEY='')
    def test_processor_uses_matching_reply_example_as_primary_response(self, get_ai_service, whatsapp_client):
        ReplyExample.objects.create(
            incoming_message='kahan ho?',
            bilal_reply='Ghar pe hoon, thori dair mein nikalta hoon.',
        )

        result = process_inbound_text(phone_number='15551234567', text='kithe a?', whatsapp_message_id='wamid.1')

        self.assertEqual(result, {'status': 'replied'})
        get_ai_service.assert_not_called()
        whatsapp_client.return_value.send_text.assert_called_once_with('15551234567', 'Ghar pe hoon, thori dair mein nikalta hoon.')

    @patch('assistant.services.processor.WhatsAppClient')
    @patch('assistant.services.processor.get_ai_service')
    @override_settings(GEMINI_API_KEY='')
    def test_processor_generates_normal_reply_when_no_relevant_example_exists(self, get_ai_service, whatsapp_client):
        ai_service = Mock()
        ai_service.generate_reply.return_value = 'Normal generated reply'
        get_ai_service.return_value = ai_service

        result = process_inbound_text(phone_number='15551234567', text='Project update?', whatsapp_message_id='wamid.2')

        self.assertEqual(result, {'status': 'replied'})
        ai_service.generate_reply.assert_called_once()
        kwargs = ai_service.generate_reply.call_args.kwargs
        self.assertNotIn(AssistantSettings.singleton().unavailable_message, kwargs['instructions'].split('\n\n')[0])
        self.assertEqual(kwargs['latest_message'], 'Project update?')
        self.assertIsInstance(kwargs['contact'], Contact)
        self.assertEqual(kwargs['history'], [])
        whatsapp_client.return_value.send_text.assert_called_once_with('15551234567', 'Normal generated reply')
