"""One model configuration shared by HSN reports and the intelligence workspace."""
import os
import re

DEFAULT_MODELS = {'gemini': 'gemini-2.5-flash', 'groq': 'llama-3.3-70b-versatile',
                  'mistral': 'mistral-small-latest', 'nvidia': 'meta/llama-3.3-70b-instruct'}


def models():
    result = {}
    for provider, default in DEFAULT_MODELS.items():
        value = os.getenv(provider.upper() + '_MODEL', default)
        # Gemini model is part of a URL path; other providers use a JSON field.
        pattern = r'[A-Za-z0-9._-]+' if provider == 'gemini' else r'[A-Za-z0-9._/-]+'
        result[provider] = value if re.fullmatch(pattern, value) and '..' not in value else default
    return result
