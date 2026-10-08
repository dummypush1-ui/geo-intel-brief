# Copyright (c) 2026 Push. All rights reserved.
"""Exact stored labels; bounded queries over the supplied snapshot only."""
ALLOWED = {'country', 'category', 'project', 'q', 'code'}


def parse_filters(args):
    if any(k not in ALLOWED for k in args):
        raise ValueError('Unsupported filter')
    filters = {}
    for k in ALLOWED:
        values = args.getlist(k) if hasattr(args, 'getlist') else [args.get(k, '')]
        if len(values) > 1 or any(type(v) is not str or len(v) > (200 if k == 'q' else 100) or any(ord(c) < 32 or ord(c) == 127 for c in v) for v in values):
            raise ValueError('Invalid filter')
        filters[k] = values[0] if values else ''
    if filters['project'] not in ('', 'geo', 'brics'):
        raise ValueError('Unknown project')
    if filters['code'] and (not filters['code'].isascii() or not filters['code'].isdigit() or not 2 <= len(filters['code']) <= 12):
        raise ValueError('Exact numeric code required')
    return filters


def text(row, key):
    value = row.get(key)
    return value if type(value) is str else ''


def filter_snapshot(data, filters):
    options = {k: sorted({text(r, k) for r in data['items'] if text(r, k)}) for k in ('original_country', 'category', 'project')}
    rows = []
    for row in data['items']:
        if any(filters[k] and text(row, field) != filters[k] for k, field in (('country', 'original_country'), ('category', 'category'), ('project', 'project'))):
            continue
        if filters['q'] and filters['q'].casefold() not in ' '.join(text(row, k) for k in ('title', 'summary', 'source', 'original_country')).casefold():
            continue
        if filters['code'] and not any(m.get('code') == filters['code'] for m in (row.get('trade_context') or []) if type(m) is dict):
            continue
        rows.append(row)
    return {**data, 'items': rows, 'count': len(rows), 'supplied_count': data['count'], 'filters': filters, 'options': options}


def apply_filters(data, args):
    return filter_snapshot(data, parse_filters(args))
