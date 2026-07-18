import logging
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from assistant.models import AssistantSettings, Contact, Conversation, Message
from assistant.serializers import AssistantSettingsSerializer, ContactSerializer, ConversationSerializer, MessageSerializer
from assistant.services.processor import process_inbound_text

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def whatsapp_webhook(request):
    if request.method == 'GET':
        if request.query_params.get('hub.mode') == 'subscribe' and request.query_params.get('hub.verify_token') == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(request.query_params.get('hub.challenge', ''))
        return Response({'detail': 'Invalid verification token'}, status=status.HTTP_403_FORBIDDEN)

    try:
        for entry in request.data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                contacts = {c.get('wa_id'): c.get('profile', {}).get('name', '') for c in value.get('contacts', [])}
                for message in value.get('messages', []):
                    if message.get('type') != 'text':
                        continue
                    phone = message.get('from')
                    process_inbound_text(
                        phone_number=phone,
                        text=message.get('text', {}).get('body', ''),
                        whatsapp_message_id=message.get('id', ''),
                        raw_payload=message,
                        profile_name=contacts.get(phone, ''),
                    )
    except Exception:
        logger.exception('Failed to process WhatsApp webhook')
        return Response({'detail': 'Webhook accepted with processing error'}, status=status.HTTP_202_ACCEPTED)
    return Response({'status': 'ok'})


class AssistantSettingsViewSet(viewsets.ModelViewSet):
    queryset = AssistantSettings.objects.all()
    serializer_class = AssistantSettingsSerializer
    permission_classes = [IsAdminUser]


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all().order_by('-updated_at')
    serializer_class = ContactSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def takeover(self, request, pk=None):
        contact = self.get_object()
        contact.human_takeover = True
        contact.save(update_fields=['human_takeover', 'updated_at'])
        return Response(self.get_serializer(contact).data)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        contact = self.get_object()
        contact.human_takeover = False
        contact.save(update_fields=['human_takeover', 'updated_at'])
        return Response(self.get_serializer(contact).data)


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Conversation.objects.select_related('contact').all().order_by('-updated_at')
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser]


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.select_related('conversation__contact').all().order_by('-created_at')
    serializer_class = MessageSerializer
    permission_classes = [IsAdminUser]
