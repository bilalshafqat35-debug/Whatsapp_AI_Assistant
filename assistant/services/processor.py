import logging
from django.db import IntegrityError, transaction
from django.utils import timezone
from assistant.models import AssistantSettings, Contact, Conversation, Message
from assistant.services.ai import get_ai_service
from assistant.services.safety import escalation_reason
from assistant.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


def process_inbound_text(*, phone_number, text, whatsapp_message_id='', raw_payload=None, profile_name=''):
    raw_payload = raw_payload or {}
    settings = AssistantSettings.singleton()
    contact, _ = Contact.objects.get_or_create(phone_number=phone_number, defaults={'display_name': profile_name})
    if profile_name and not contact.display_name:
        contact.display_name = profile_name
    contact.last_seen_at = timezone.now()
    contact.save(update_fields=['display_name', 'last_seen_at', 'updated_at'])
    conversation, _ = Conversation.objects.get_or_create(contact=contact)

    try:
        with transaction.atomic():
            inbound = Message.objects.create(
                conversation=conversation, whatsapp_message_id=whatsapp_message_id, direction=Message.Direction.INBOUND,
                sender_type=Message.SenderType.CONTACT, text=text, raw_payload=raw_payload,
            )
    except IntegrityError:
        logger.info('Duplicate WhatsApp message ignored: %s', whatsapp_message_id)
        return {'status': 'duplicate'}

    conversation.last_message_at = inbound.created_at
    conversation.save(update_fields=['last_message_at', 'updated_at'])

    if not settings.auto_reply_enabled or contact.human_takeover or contact.is_blocked:
        return {'status': 'stored_no_reply'}

    reason = escalation_reason(text)
    if reason:
        conversation.mark_escalated(reason)
        return {'status': 'escalated', 'reason': reason}

    instructions = f"{settings.unavailable_message}\n\nOwner instructions:\n{settings.custom_instructions}\n\nNever answer sensitive, urgent, financial, OTP, password, or highly personal requests; escalate instead."
    history = conversation.messages.exclude(pk=inbound.pk)
    reply = get_ai_service().generate_reply(instructions=instructions, contact=contact, history=list(history), latest_message=text)
    WhatsAppClient().send_text(phone_number, reply)
    Message.objects.create(conversation=conversation, direction=Message.Direction.OUTBOUND, sender_type=Message.SenderType.AI, text=reply)
    return {'status': 'replied'}
