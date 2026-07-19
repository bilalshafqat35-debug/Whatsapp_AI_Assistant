import re

from assistant.models import ReplyExample

MAX_REPLY_EXAMPLES = 5
TOKEN_PATTERN = re.compile(r"[\w']+", re.UNICODE)


def _tokens(text):
    return {token.lower() for token in TOKEN_PATTERN.findall(text or '') if len(token) > 1}


def relevant_reply_examples(latest_message, *, limit=MAX_REPLY_EXAMPLES):
    """Return active reply examples ordered by simple lexical relevance."""
    message_tokens = _tokens(latest_message)
    examples = list(ReplyExample.objects.filter(is_active=True))

    def score(example):
        example_tokens = _tokens(example.incoming_message)
        overlap = len(message_tokens & example_tokens)
        exact_bonus = 2 if latest_message.lower().strip() in example.incoming_message.lower() else 0
        return overlap + exact_bonus

    ranked = sorted(examples, key=lambda example: (score(example), example.updated_at, example.pk), reverse=True)
    return ranked[:limit]


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
