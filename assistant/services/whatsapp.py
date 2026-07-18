import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self):
        self.base_url = f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}'

    def send_text(self, to, text):
        if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            logger.warning('WhatsApp credentials are not configured; skipping outbound message to %s', to)
            return {'skipped': True, 'reason': 'missing_credentials'}
        response = requests.post(
            f'{self.base_url}/messages',
            headers={'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}', 'Content-Type': 'application/json'},
            json={'messaging_product': 'whatsapp', 'to': to, 'type': 'text', 'text': {'body': text}},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
