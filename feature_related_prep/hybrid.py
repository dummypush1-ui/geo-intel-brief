# Copyright (c) 2026 Push. All rights reserved.
"""Keywords first; uncertain product/code matches held for supplied AI review.

No routes, clients, callbacks, environment, database, network or prompt export.
Inputs are bounded public fixture fields only, not a complete news archive.
Supplied AI records are unverified caller data, never authenticated provider
responses. Hash binding prevents accidental reuse, not forgery. Decisions are
related-news suggestions, never tariff, legal, duty or factual verification.
"""
from hashlib import sha256
import json
import math
import re
from integration.relevance import match
from integration.taxonomy import country_code

CONTEXT_FIELDS = {'code', 'system', 'edition', 'country', 'product_terms'}
ARTICLE_FIELDS = {'article_key', 'title', 'summary'}
REVIEW_FIELDS = {'article_hash', 'context_hash', 'provider', 'related', 'confidence', 'reason'}
PROVIDERS = {'groq', 'gemini', 'mistral'}


def _text(value, limit):
    if (type(value) is not str or len(value) > limit
            or any(0xD800 <= ord(c) <= 0xDFFF or ord(c) < 32 and c not in '\n\t' for c in value)):
        raise ValueError('Bounded plain text required')
    return value


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _context(value):
    if type(value) is not dict or set(value) != CONTEXT_FIELDS:
        raise ValueError('Closed context required')
    clean = {k: _text(value[k], 200) for k in CONTEXT_FIELDS - {'product_terms'}}
    if clean['code'] and not re.fullmatch(r'\d{6,12}', clean['code'], re.ASCII):
        raise ValueError('ASCII trade code required')
    if clean['country'] and not country_code(clean['country']):
        raise ValueError('Known country required')
    terms = value['product_terms']
    if type(terms) is not list or len(terms) > 20:
        raise ValueError('Bounded product terms required')
    clean['product_terms'] = [_text(t, 200).strip() for t in terms]
    if not clean['code'] and not any(len(t) >= 3 for t in clean['product_terms']):
        raise ValueError('Product term or trade code required')
    return clean


def plan(context, articles, reviews=None):
    """Return keyword decisions and holds; never execute an AI review."""
    context = _context(context)
    if type(articles) is not list or len(articles) > 100:
        raise ValueError('Bounded plain article list required')
    rows, keys = [], set()
    for row in articles:
        if type(row) is not dict or set(row) != ARTICLE_FIELDS:
            raise ValueError('Closed public fixture row required')
        clean = {k: _text(row[k], 16000 if k == 'summary' else 1000) for k in ARTICLE_FIELDS}
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}', clean['article_key']) or clean['article_key'] in keys:
            raise ValueError('Unique opaque article key required')
        if not clean['title'].strip():
            raise ValueError('Title required')
        keys.add(clean['article_key'])
        rows.append(clean)
    if len(json.dumps([context, rows], ensure_ascii=True).encode()) > 256 * 1024:
        raise ValueError('Fixture byte cap exceeded')
    context_hash = _hash(context)
    decisions, held = [], set()
    for row in rows:
        result = match(context, row)
        signals = {r['type'] for r in result['reasons']}
        product = bool(signals & {'product_term', 'explicit_code'})
        decision = 'reject' if not product else 'accept' if 'country_context' in signals else 'held'
        digest = _hash(row)
        if decision == 'held':
            held.add(digest)
        decisions.append({'article_key': row['article_key'], 'article_hash': digest,
                          'context_hash': context_hash, 'decision': decision,
                          'basis': 'keywords', 'reasons': result['reasons'],
                          'ai_required': decision == 'held', 'provider_verified': False,
                          'duty_change_verified': False})
    reviews = [] if reviews is None else reviews
    if type(reviews) is not list or len(reviews) > 100:
        raise ValueError('Bounded supplied review list required')
    supplied = {}
    for review in reviews:
        if type(review) is not dict or set(review) != REVIEW_FIELDS:
            raise ValueError('Closed supplied review required')
        for key in ('article_hash', 'context_hash'):
            if type(review[key]) is not str or not re.fullmatch(r'[0-9a-f]{64}', review[key]):
                raise ValueError('SHA256 binding required')
        digest = review['article_hash']
        if digest not in held or review['context_hash'] != context_hash or digest in supplied:
            raise ValueError('Unique held article/context binding required')
        if type(review['provider']) is not str or review['provider'] not in PROVIDERS:
            raise ValueError('Allowed provider label required')
        confidence = review['confidence']
        if (type(review['related']) is not bool or type(confidence) not in (int, float)
                or not math.isfinite(confidence) or not 0 <= confidence <= 1):
            raise ValueError('Boolean decision and finite confidence required')
        reason = _text(review['reason'], 500)
        if not reason.strip():
            raise ValueError('Review reason required')
        supplied[digest] = dict(review)
    for item in decisions:
        review = supplied.get(item['article_hash'])
        if review is not None:
            item['basis'] = 'supplied_unverified_ai'
            item['review'] = review
            if review['confidence'] >= 0.8:
                item['decision'] = 'accept' if review['related'] else 'reject'
                item['ai_required'] = False
    return {'mode': 'supplied_sample_only', 'suggestions_only': True,
            'provider_calls': 0, 'mounted': False, 'decisions': decisions}
