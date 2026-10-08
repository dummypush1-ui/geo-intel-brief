# Copyright (c) 2026 Push. All rights reserved.
"""Pure reviewed-input Finder mount policy. No transport or authorization grant.

Assertions supplied by caller are preparation inputs, not verified account or
owner evidence. Return stays unmounted. No shared proxy, keys, prompts, calls,
paid fallback or automatic model selection. Later execution must verify grants.
"""
from copy import deepcopy
import re

FIELDS = {'provider', 'model', 'endpoint', 'model_checked_at', 'free_tier_checked_at',
          'disclosure_checked_at', 'free_only_account', 'disclosure_confirmed',
          'per_report_requests', 'per_report_tokens', 'daily_requests',
          'request_bytes', 'response_bytes', 'attempt_seconds', 'report_seconds'}
MODELS = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}')
ENDPOINTS = {'groq': 'https://api.groq.com/openai/v1/chat/completions',
             'mistral': 'https://api.mistral.ai/v1/chat/completions'}
GEMINI = 'https://generativelanguage.googleapis.com/v1beta/models/'


def prepare(configs, *, checked_at):
    if type(checked_at) is not int or not 0 <= checked_at <= 2**53:
        raise ValueError('Fixed epoch clock required')
    if type(configs) is not list or not 1 <= len(configs) <= 3:
        raise ValueError('Explicit provider choices required')
    seen, out = set(), []
    caps = {'per_report_requests': (1, 12), 'per_report_tokens': (1, 24000),
            'daily_requests': (1, 1000), 'request_bytes': (1, 65536),
            'response_bytes': (1, 262144), 'attempt_seconds': (1, 15), 'report_seconds': (1, 120)}
    for row in configs:
        if type(row) is not dict or set(row) != FIELDS:
            raise ValueError('Closed provider review required')
        provider, model = row['provider'], row['model']
        if type(provider) is not str or provider not in ('groq', 'gemini', 'mistral') or provider in seen:
            raise ValueError('Unique allowed provider required')
        seen.add(provider)
        if type(model) is not str or not MODELS.fullmatch(model):
            raise ValueError('Explicit bounded model name required')
        endpoint = GEMINI + model + ':generateContent' if provider == 'gemini' else ENDPOINTS[provider]
        if row['endpoint'] != endpoint or type(row['endpoint']) is not str:
            raise ValueError('Exact official HTTPS endpoint required; no proxy/query/redirect')
        for name in ('model_checked_at', 'free_tier_checked_at', 'disclosure_checked_at'):
            stamp = row[name]
            if type(stamp) is not int or not 0 <= checked_at - stamp <= 86400:
                raise ValueError('Fresh caller review within 24h required')
        if row['free_only_account'] is not True or row['disclosure_confirmed'] is not True:
            raise ValueError('Explicit free-only and disclosure review inputs required')
        for field, (low, high) in caps.items():
            if type(row[field]) is not int or not low <= row[field] <= high:
                raise ValueError('Finite bounded report/quota caps required')
        if row['attempt_seconds'] > row['report_seconds'] or row['per_report_requests'] > row['daily_requests']:
            raise ValueError('Consistent attempt/report/day budgets required')
        out.append(deepcopy(row))
    # Per-provider limits must also fit one overall report, not multiply with
    # failover. These are upper-bound budgets, not quota availability proofs.
    requests = sum(r['per_report_requests'] for r in out)
    tokens = sum(r['per_report_tokens'] for r in out)
    if requests > 12 or tokens > 24000:
        raise ValueError('Combined report request/token budget exceeded')
    return {'mode': 'review_inputs_only_not_authority', 'mounted': False,
            'provider_calls': 0, 'provider_account_verified': False,
            'owner_permission_verified': False, 'transport_implemented': False,
            'shared_proxy_allowed': False, 'paid_fallback_allowed': False,
            'configs': out, 'report_requests_cap': requests,
            'report_tokens_cap': tokens, 'report_seconds_cap': min(r['report_seconds'] for r in out),
            'on_exhaustion': 'static_report_fallback', 'checked_at': checked_at}
