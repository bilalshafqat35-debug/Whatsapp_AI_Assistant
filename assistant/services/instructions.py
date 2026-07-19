from assistant.services.reply_examples import format_reply_examples, relevant_reply_examples

SAFETY_INSTRUCTIONS = 'Never answer sensitive, urgent, financial, OTP, password, or highly personal requests; escalate instead.'


def build_ai_instructions(settings, *, latest_message=''):
    sections = [
        settings.unavailable_message,
        f'Owner instructions:\n{settings.custom_instructions}',
        SAFETY_INSTRUCTIONS,
    ]
    examples = format_reply_examples(relevant_reply_examples(latest_message))
    if examples:
        sections.append(examples)
    return '\n\n'.join(sections)
