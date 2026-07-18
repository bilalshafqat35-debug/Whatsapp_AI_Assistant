from abc import ABC, abstractmethod
from django.conf import settings


class AIService(ABC):
    @abstractmethod
    def generate_reply(self, *, instructions, contact, history, latest_message):
        raise NotImplementedError


class OpenAIService(AIService):
    def generate_reply(self, *, instructions, contact, history, latest_message):
        if not settings.OPENAI_API_KEY:
            return 'Thanks for your message. I am currently unavailable and will respond personally as soon as possible.'
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        messages = [{'role': 'system', 'content': instructions}]
        for item in history[-20:]:
            role = 'assistant' if item.sender_type == 'ai' else 'user'
            messages.append({'role': role, 'content': item.text})
        messages.append({'role': 'user', 'content': latest_message})
        response = client.chat.completions.create(model=settings.OPENAI_MODEL, messages=messages, temperature=0.4)
        return response.choices[0].message.content.strip()


def get_ai_service():
    return OpenAIService()
