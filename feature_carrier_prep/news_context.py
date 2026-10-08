"""Bounded exact-phrase context from real public-news field boundary, no I/O."""
import re
from integration.public_news import public_news_row, PUBLIC_NEWS_FIELDS
from .models import bounded, text


def prepare(articles, carrier):
    terms = [text(carrier['name'])] + [text(t) for t in bounded(carrier['aliases'], 10)]
    if any(len(t) < 3 for t in terms):
        raise ValueError('Distinctive reviewed aliases required')
    output, seen = [], set()
    for row in bounded(articles, 100):
        if type(row) is not dict or set(row) - set(PUBLIC_NEWS_FIELDS):
            raise ValueError('Already sanitized canonical article required')
        clean = public_news_row(row)
        key = text(clean.get('article_key'), 120)
        if key in seen:
            raise ValueError('Unique loaded article keys required')
        seen.add(key)
        title = text(clean.get('title'), 1000)
        summary = clean.get('summary', '')
        if type(summary) is not str or len(summary) > 16000:
            raise ValueError('Bounded public summary required')
        haystack = title + '\n' + summary
        matches = [term for term in terms if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', haystack)]
        if matches:
            # Only expose the fields needed by context, never raw input values.
            output.append({'article_key': key, 'title': title, 'matched_aliases': matches,
                           'match': 'exact_case_sensitive_phrase_context_not_verification'})
    return {'items': output, 'scope': 'loaded_sanitized_view', 'not_total_database': True,
            'live_tracking': False, 'risk_score': None}
