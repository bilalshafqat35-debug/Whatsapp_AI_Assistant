import re

SENSITIVE_PATTERNS = {
    'urgent or emergency': r'\b(urgent|emergency|asap|hospital|police|accident|death|dead|suicide)\b',
    'financial': r'\b(bank|payment|invoice|loan|transfer|account number|credit card|debit card|salary|tax)\b',
    'otp or password': r'\b(otp|one[- ]?time|verification code|password|passcode|pin)\b',
    'highly personal': r'\b(medical|diagnosis|legal|lawyer|court|divorce|pregnant|private|secret)\b',
}


def escalation_reason(text):
    normalized = text.lower()
    for reason, pattern in SENSITIVE_PATTERNS.items():
        if re.search(pattern, normalized):
            return reason
    return ''
