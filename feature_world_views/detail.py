# Copyright (c) 2026 Push. All rights reserved.
"""Exact-key drill-down within supplied snapshot; no arbitrary URL fetch."""
import re


def detail(data, key):
    if not re.fullmatch(r'[a-f0-9]{64}', key):
        raise ValueError('Exact article key required')
    row = next((row for row in data['items'] if row['article_key'] == key), None)
    if row is None:
        return None
    return {'item': row, 'scope': data['scope'], 'not_database_totals': True,
            'evidence': {'article_url': row['url'], 'published_at': row['published_at'],
                'collected_at': row['collected_at'], 'trade_match': 'explicit_code_in_article',
                'tariff_verified': False}, 'related': [
                {'article_key': other['article_key'], 'title': other['title'],
                 'basis': 'shared_exact_code' if {m['code'] for m in row['trade_context']} & {m['code'] for m in other['trade_context']} else 'exact_country_label'}
                for other in data['items'] if other['article_key'] != key and (
                    {m['code'] for m in row['trade_context']} & {m['code'] for m in other['trade_context']} or
                    row['original_country'] and row['original_country'] == other['original_country'])][:20]}
