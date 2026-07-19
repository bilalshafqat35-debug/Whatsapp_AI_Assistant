import json
import logging
import re

from django.conf import settings

from assistant.models import ReplyExample

logger = logging.getLogger(__name__)

MAX_REPLY_EXAMPLES = 5
SEMANTIC_MATCH_LIMIT = 20
MIN_SEMANTIC_SCORE = 4
TOKEN_PATTERN = re.compile(r"[\w']+", re.UNICODE)

INTENT_SYNONYMS = {
    'where': {
        'where', 'whr', 'kahan', 'kaha', 'kidhar', 'kithe', 'kithay', 'kithey', 'kithe a', 'kithe aa',
        'kithey', 'kithy', 'location', 'loc', 'کہاں', 'کدھر', 'کتھے', 'کیتھے', 'ਕਿੱਥੇ',
    },
    'you': {'you', 'u', 'tum', 'tu', 'ap', 'aap', 'ho', 'hai', 'hain', 'a', 'aa', 'ہیں', 'ہو', 'آپ', 'تسی'},
    'coming': {'coming', 'come', 'arrive', 'aana', 'ana', 'ao', 'aa', 'atay', 'ate', 'آنا', 'آ رہے'},
    'busy': {'busy', 'free', 'available', 'farigh', ' فارغ', 'مصروف'},
    'plan': {'plan', 'scene', 'program', 'پلان', 'سین'},
    'thanks': {'thanks', 'thank', 'thx', 'shukriya', 'shukria', 'meharbani', 'شکریہ'},
    'greeting': {'hi', 'hello', 'hey', 'salam', 'salaam', 'assalam', 'السلام', 'سلام'},
    'time': {'when', 'time', 'kab', 'kado', 'کب', 'کدو', 'وقت'},
    'reason': {'why', 'kyun', 'q', 'kiun', 'کیوں'},
    'wellbeing': {'how', 'kaise', 'kese', 'kidda', 'kida', 'kya haal', 'haal', 'کیسے', 'حال'},
}

CANONICAL_TOKEN_BY_SYNONYM = {
    synonym: canonical
    for canonical, synonyms in INTENT_SYNONYMS.items()
    for synonym in synonyms
}

PHRASE_REPLACEMENTS = {
    'kaha pe ho': 'where you',
    'kahan ho': 'where you',
    'kidhar ho': 'where you',
    'kithe a': 'where you',
    'kithe aa': 'where you',
    'kithe ho': 'where you',
    'where are you': 'where you',
    'where r u': 'where you',
    'kya haal': 'wellbeing',
}


def _normalize_text(text):
    normalized = (text or '').lower().strip()
    normalized = re.sub(r'[^\w\s]', ' ', normalized, flags=re.UNICODE)
    normalized = re.sub(r'\s+', ' ', normalized)
    for phrase, replacement in PHRASE_REPLACEMENTS.items():
        normalized = normalized.replace(phrase, replacement)
    return normalized


def _tokens(text):
    normalized = _normalize_text(text)
    tokens = []
    for token in TOKEN_PATTERN.findall(normalized):
        if len(token) <= 1 and token not in {'u', 'a', 'q'}:
            continue
        tokens.append(CANONICAL_TOKEN_BY_SYNONYM.get(token, token))
    return set(tokens)


def _semantic_score(message, example_message):
    message_tokens = _tokens(message)
    example_tokens = _tokens(example_message)
    overlap = len(message_tokens & example_tokens)
    exact_bonus = 3 if _normalize_text(message) == _normalize_text(example_message) else 0
    subset_bonus = 2 if message_tokens and message_tokens <= example_tokens else 0
    return overlap + exact_bonus + subset_bonus


def relevant_reply_examples(latest_message, *, limit=MAX_REPLY_EXAMPLES):
    """Return active reply examples ordered by multilingual semantic relevance."""
    examples = list(ReplyExample.objects.filter(is_active=True))
    ranked = sorted(
        examples,
        key=lambda example: (_semantic_score(latest_message, example.incoming_message), example.updated_at, example.pk),
        reverse=True,
    )
    return ranked[:limit]


def find_semantic_reply_example(latest_message, *, limit=SEMANTIC_MATCH_LIMIT):
    """Return the best active ReplyExample that matches the latest message intent."""
    examples = relevant_reply_examples(latest_message, limit=limit)
    if not examples:
        return None

    gemini_match = _gemini_match(latest_message, examples)
    if gemini_match is not None:
        return gemini_match

    best = examples[0]
    if _semantic_score(latest_message, best.incoming_message) >= MIN_SEMANTIC_SCORE:
        return best
    return None


def _gemini_match(latest_message, examples):
    if not settings.GEMINI_API_KEY:
        return None

    from google import genai
    from google.genai import types

    examples_payload = [
        {'id': example.pk, 'incoming_message': example.incoming_message, 'bilal_reply': example.bilal_reply}
        for example in examples
    ]
    prompt = (
        'Choose the one active reply example with the same intent as the incoming message across English, Urdu, '
        'Roman Urdu, and Punjabi variations. Match intent, not identical words. Return only JSON like '
        '{"match_id": 123} or {"match_id": null}.\n'
        f'Incoming message: {latest_message}\nReply examples: {json.dumps(examples_payload, ensure_ascii=False)}'
    )
    try:
        response = genai.Client(api_key=settings.GEMINI_API_KEY).models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0),
        )
        data = json.loads((response.text or '').strip())
    except Exception as exc:
        logger.warning('Gemini reply-example semantic match failed; using local matcher: %s', exc)
        return None

    match_id = data.get('match_id')
    if match_id is None:
        return None
    for example in examples:
        if str(example.pk) == str(match_id):
            return example
    return None


def format_reply_examples(examples):
    if not examples:
        return ''

    lines = [
        'Reply examples for Bilal style:',
        'Use these examples only as tone and wording guidance. Do not copy facts that are not relevant to the current conversation.',
    ]
    for index, example in enumerate(examples, start=1):
        lines.append(f"Example {index} incoming: {example.incoming_message}")
        lines.append(f"Example {index} Bilal-style reply: {example.bilal_reply}")
    return '\n'.join(lines)
