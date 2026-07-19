import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)

FALLBACK_REPLY = 'Thanks for your message. I am currently unavailable and will respond personally as soon as possible.'


class AIService(ABC):
    @abstractmethod
    def generate_reply(self, *, instructions, contact, history, latest_message, fallback_reply=FALLBACK_REPLY):
        raise NotImplementedError


class GeminiAIService(AIService):
    """AI service implementation backed by the official Google Gen AI SDK."""

    def generate_reply(self, *, instructions, contact, history, latest_message, fallback_reply=FALLBACK_REPLY):
        if not settings.GEMINI_API_KEY:
            logger.error('GEMINI_API_KEY is missing; using fallback reply.')
            return fallback_reply

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        contents = self._build_contents(history=history, latest_message=latest_message, types=types)

        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=instructions,
                    temperature=0.4,
                ),
            )
        except Exception as exc:
            if self._is_quota_error(exc):
                logger.error('Gemini API quota exhausted or rate limited: %s', exc)
            else:
                logger.exception('Gemini API request failed: %s', exc)
            return fallback_reply

        reply = (response.text or '').strip()
        if not reply:
            logger.error('Gemini API returned an empty response; using fallback reply.')
            return fallback_reply
        return reply

    def _build_contents(self, *, history, latest_message, types):
        contents = []
        for item in history[-20:]:
            role = 'model' if item.sender_type == 'ai' else 'user'
            if item.text:
                contents.append(types.Content(role=role, parts=[types.Part(text=item.text)]))
        contents.append(types.Content(role='user', parts=[types.Part(text=latest_message)]))
        return contents

    def _is_quota_error(self, exc):
        status_code = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
        status = str(getattr(exc, 'status', '')).upper()
        message = str(exc).lower()
        return status_code == 429 or 'quota' in message or 'rate' in message or status == 'RESOURCE_EXHAUSTED'


def get_ai_service():
    return GeminiAIService()
