# Copyright (c) 2026 Push. All rights reserved.
"""Bounded news and exact-code trade context. Never infer tariffs or risk."""
from datetime import datetime
from integration.news_view import views
from integration.public_news import public_news_row, READ_STORE_FIELDS

MAX_ROWS = 100
TEXT_LIMIT = 8000


def snapshot(raw, finder_index=None):
    if type(raw) is not dict or not set(raw) <= {'geo', 'brics'}:
        raise ValueError('Approved project rows required')
    safe = {}
    truncated = False
    for project, rows in raw.items():
        if type(rows) is not list:
            raise ValueError('Bounded project rows required')
        safe[project] = []
        truncated = truncated or len(rows) > MAX_ROWS
        for row in rows[:MAX_ROWS]:
            if type(row) is not dict:
                raise ValueError('Plain row required')
            clean = {}
            for key in READ_STORE_FIELDS:
                value = row.get(key)
                if key in ('title', 'url') and (type(value) is not str or not value.strip() or len(value) > TEXT_LIMIT):
                    break
                if key in ('published','created_at','collected_at') and type(value) is datetime and value.tzinfo is not None:
                    clean[key] = value
                if type(value) is str and len(value) <= TEXT_LIMIT:
                    clean[key] = value
            else:
                safe[project].append(clean)
    items = []
    seen = set()
    for row in views(safe):
        if row['article_key'] in seen:
            continue
        seen.add(row['article_key'])
        public = public_news_row(row)
        # The preserved index matches explicit HS/HSN codes only, not products.
        matches = finder_index.for_article(public) if finder_index else []
        public['trade_context'] = [dict(code=m['code'], system=m['system'],
            system_name=m['system_name'], system_index=m['system_index'],
            evidence='explicit_code_in_article', scope='bundled_finder_snapshot') for m in matches]
        items.append(public)
    items.sort(key=lambda r: (r['title'].casefold(), r['article_key']))
    items.sort(key=lambda r: r['collected_at'] or '', reverse=True)
    return {'items': items, 'count': len(items), 'limit_per_project': MAX_ROWS,
            'scope': 'supplied_read_view', 'not_database_totals': True, 'truncated': truncated,
            'trade_state': 'bundled_exact_code_context' if finder_index else 'not_supplied',
            'live_trade_lookup': False, 'tariff_verification': False}
