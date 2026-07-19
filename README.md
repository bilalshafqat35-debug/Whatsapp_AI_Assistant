# WhatsApp AI Assistant

A personal WhatsApp AI auto-reply assistant built with Python, Django, Django REST Framework, and the official Meta WhatsApp Cloud API.

## Features

- Auto-reply on/off setting managed in Django Admin or REST API.
- Contact, conversation, and message history models with separate history per WhatsApp contact.
- Custom owner instructions for the AI assistant.
- Human takeover mode per contact; when enabled, the bot stores messages but stops replying.
- WhatsApp Cloud API webhook verification and inbound text processing.
- AI service abstraction with a Google Gemini implementation and a safe fallback when no API key, quota, or API response is available.
- Escalation instead of auto-reply for urgent, sensitive, financial, OTP/password, or highly personal messages.
- Duplicate WhatsApp message protection through a unique message-id constraint.
- Environment-variable based configuration; no real secrets are committed.

## Project structure

```text
assistant/              Core Django app
assistant/models.py     Settings, contacts, conversations, messages
assistant/services/     AI, safety, WhatsApp API, and message processor services
assistant/views.py      DRF viewsets and WhatsApp webhook
config/                 Django project settings and URLs
```

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies, including the official Google Gen AI Python SDK:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables and fill local values only:

   ```bash
   cp .env.example .env
   ```

4. Run migrations and create an admin user:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Start the server:

   ```bash
   python manage.py runserver
   ```

6. Open the admin dashboard at `http://127.0.0.1:8000/admin/`.

## Gemini configuration

This project uses the official Google Gen AI Python SDK (`google-genai`) through the existing `AIService` abstraction. Configure Gemini with environment variables:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash-lite
```

`GEMINI_MODEL` defaults to `gemini-2.5-flash-lite` when it is not set. If `GEMINI_API_KEY` is missing, Gemini quota is exhausted, the API is rate-limited, or the API request fails, the assistant logs the error and sends a safe fallback reply instead of crashing the webhook.

## WhatsApp webhook

Configure the Meta WhatsApp Cloud API webhook URL as:

```text
https://YOUR_DOMAIN/api/webhooks/whatsapp/
```

Use `WHATSAPP_VERIFY_TOKEN` from your `.env` file as the webhook verification token. Set `WHATSAPP_ACCESS_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` only in your deployed environment.

## REST API

Admin-authenticated endpoints are available under `/api/`:

- `/api/settings/`
- `/api/contacts/`
- `/api/contacts/{id}/takeover/`
- `/api/contacts/{id}/release/`
- `/api/conversations/`
- `/api/messages/`

## Safety behavior

The processor stores every inbound text message. It auto-replies only when global auto-reply is enabled and the contact is not blocked or under human takeover. Messages matching sensitive categories are marked escalated and are not answered by the AI.
