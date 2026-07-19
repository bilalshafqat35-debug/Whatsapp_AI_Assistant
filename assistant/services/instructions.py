from assistant.services.reply_examples import format_reply_examples, relevant_reply_examples

SAFETY_INSTRUCTIONS = 'Never answer sensitive, urgent, financial, OTP, password, or highly personal requests; escalate instead.'


def build_ai_instructions(settings, *, latest_message=''):
    sections = [
        f'Owner instructions:\n{settings.custom_instructions}',
        SAFETY_INSTRUCTIONS,
        'Generate a normal conversational reply using the custom instructions and conversation history. Do not prepend an unavailable notice unless no useful reply can be generated.',
    ]
    examples = format_reply_examples(relevant_reply_examples(latest_message))
    if examples:
        sections.append(examples)
    return '\n\n'.join(sections)
