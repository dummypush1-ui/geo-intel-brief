"""Country read view over supplied normalized news. No country inference or I/O.

Copyright (c) 2026 Push. Independently written for this project.
"""
from collections import Counter
from integration.public_news import public_news_row

MAX_LABEL = 100
LIMIT = 100

def country_page(rows, country='', project=''):
    if project not in ('', 'geo', 'brics') or not isinstance(country, str) or len(country) > MAX_LABEL or any((ord(c) < 32 or ord(c) == 127) for c in country):
        raise ValueError('Invalid country or project')
    # Exact stored labels only. No text-mention guess, geocoding, or ISO alias merge.
    labels = sorted({r['original_country'] for r in rows if r['original_country'].strip() and r['original_country'].strip() == r['original_country'] and len(r['original_country']) <= MAX_LABEL and not any((ord(c) < 32 or ord(c) == 127) for c in r['original_country'])}, key=lambda s:(s.casefold(), s))
    selected = [r for r in rows if country and r['original_country'] == country and (not project or r['project'] == project)]
    selected.sort(key=lambda r:(r['title'].casefold(), r['article_key']))
    selected.sort(key=lambda r:r['collected_at'] or '', reverse=True)
    count = Counter(r['project'] for r in selected)
    return {'country':country, 'project':project, 'countries':labels,
            'count':len(selected), 'project_counts':{'geo':count['geo'], 'brics':count['brics']},
            'items':[public_news_row(r) for r in selected[:LIMIT]],
            'limit':LIMIT, 'truncated':len(selected)>LIMIT, 'scope':'loaded_read_view',
            'not_total_database':True, 'country_match':'exact_original_label',
            'risk_index':None, 'risk_index_state':'not_built', 'tariff_changes_state':'not_verified',
            'watchlist_storage':'browser_only', 'delivery':False}
