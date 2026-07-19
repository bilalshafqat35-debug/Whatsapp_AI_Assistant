from django.utils import timezone

from assistant.models import AssistantSettings, Contact, Conversation, Message
from assistant.services.ai import get_ai_service
from assistant.services.instructions import build_ai_instructions
from assistant.services.safety import escalation_reason

TEST_CHAT_PHONE_NUMBER = 'local-test-chat'
TEST_CHAT_DISPLAY_NAME = 'Local Test Chat'


def get_test_conversation():
    contact, created = Contact.objects.get_or_create(
        phone_number=TEST_CHAT_PHONE_NUMBER,
        defaults={'display_name': TEST_CHAT_DISPLAY_NAME},
    )
    update_fields = []
    if not contact.display_name:
        contact.display_name = TEST_CHAT_DISPLAY_NAME
        update_fields.append('display_name')
    contact.last_seen_at = timezone.now()
    update_fields.extend(['last_seen_at', 'updated_at'])
    contact.save(update_fields=update_fields)
    conversation, _ = Conversation.objects.get_or_create(contact=contact)
    return conversation


def process_test_chat_message(text):
    settings = AssistantSettings.singleton()
    conversation = get_test_conversation()

    inbound = Message.objects.create(
        conversation=conversation,
        direction=Message.Direction.INBOUND,
        sender_type=Message.SenderType.CONTACT,
        text=text,
        raw_payload={'source': 'local_test_chat'},
    )
    conversation.last_message_at = inbound.created_at
    conversation.save(update_fields=['last_message_at', 'updated_at'])

    if not settings.auto_reply_enabled:
        return {'status': 'stored_no_reply', 'conversation': conversation, 'reply': ''}

    reason = escalation_reason(text)
    if reason:
        conversation.mark_escalated(reason)
        return {'status': 'escalated', 'reason': reason, 'conversation': conversation, 'reply': ''}

    history = list(conversation.messages.exclude(pk=inbound.pk))
    reply = get_ai_service().generate_reply(
        instructions=build_ai_instructions(settings, latest_message=text),
        contact=conversation.contact,
        history=history,
        latest_message=text,
    )
    Message.objects.create(
        conversation=conversation,
        direction=Message.Direction.OUTBOUND,
        sender_type=Message.SenderType.AI,
        text=reply,
        raw_payload={'source': 'local_test_chat'},
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=['last_message_at', 'updated_at'])
    return {'status': 'replied', 'conversation': conversation, 'reply': reply}
