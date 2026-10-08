# Copyright (c) 2026 Push. All rights reserved.
"""Bounded original renderer composition for a transaction-backed source."""
from datetime import datetime, timezone, timedelta
from feature_mail_prep.reports import _snapshot, _clock
from integration.renderer_scope import renderer
from integration.html_safety import sanitize_html
from bson import ObjectId

FIELDS = ('_id', 'title', 'summary', 'url', 'source', 'category', 'country',
          'risk_level', 'score', 'credibility', 'corroboration', 'published',
          'created_at', 'emailed')
EVENTS = ('name', 'event_date', 'source_url', 'category', 'confidence', 'description')
POLICIES = ('fetched', 'displayed')


def _rows(cursor, cap):
    rows = []
    try:
        for row in cursor:
            if len(rows) >= cap:
                raise ValueError('Mail source row cap exceeded')
            rows.append(row)
    finally:
        cursor.close()
    return rows


def _articles(rows):
    clean = []
    for row in rows:
        if type(row) is not dict or set(row) - set(FIELDS) or type(row.get('_id')) is not ObjectId:
            raise ValueError('Reviewed Geo article schema required')
        r = dict(row)
        r['_id'] = str(r['_id'])
        if any(type(r.get(k)) is not str for k in ('published', 'created_at')):
            raise ValueError('Reviewed ISO string article dates required')
        for k in ('published', 'created_at'):
            stamp = datetime.fromisoformat(r[k])
            if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0) or stamp.astimezone(timezone.utc).isoformat() != r[k]:
                raise ValueError('Canonical UTC ISO source strings required')
        if r.get('emailed') is None:
            r['emailed'] = False
        clean.append(r)
    return _snapshot(clean, [])[0]


def _aggregate(collection, pipeline, session, cap):
    return _rows(collection.aggregate(pipeline, session=session, maxTimeMS=2000), cap)


def build(collections, session, kind, now, policy):
    now = _clock(now)
    if kind not in ('digest', 'critical', 'weekly') or policy not in POLICIES:
        raise ValueError('Explicit report kind and marking policy required')
    articles, events = collections['articles'], collections['events']
    cutoff = (now - (timedelta(hours=6) if kind == 'critical' else timedelta(days=7))).isoformat() if kind != 'digest' else None
    query = {'emailed': {'$ne': True}} if kind == 'digest' else {'created_at': {'$gte': cutoff}}
    if kind == 'critical':
        query.update(risk_level='CRITICAL', mail_critical_sent={'$ne': True})
    cap = 60 if kind == 'digest' else 200 if kind == 'critical' else 20
    cursor = articles.find(query, {k: 1 for k in FIELDS}, session=session)
    rows = _articles(_rows(cursor.sort([('score', -1), ('published', -1), ('_id', -1)]).limit(cap + (1 if kind == 'critical' else 0)).max_time_ms(2000), cap))
    fetched = [r['_id'] for r in rows]
    displayed = [r['_id'] for r in rows if r['score'] >= 4] if kind == 'digest' else fetched[:]
    critical = sum(r['risk_level'] == 'CRITICAL' for r in rows)
    if kind == 'digest':
        today = now.date()
        q = {'event_date': {'$gte': today.isoformat(), '$lte': (today + timedelta(days=90)).isoformat()}}
        raw_events = _rows(events.find(q, {**{k: 1 for k in EVENTS}, '_id': 0}, session=session).sort('event_date', 1).limit(201).max_time_ms(2000), 200)
        event_rows = _snapshot([], raw_events)[1]
        html, critical, _ = renderer('geo_digest', {'unemailed_articles': lambda: rows,
                    'upcoming_events': lambda days: event_rows}, now=now)()
        skip = not displayed and not critical and not event_rows
        subject = 'Geo Intel Brief - ' + now.strftime('%d %b %Y %H:%M UTC')
    elif kind == 'critical':
        html = renderer('geo_critical', {}, now=now)(rows) if rows else ''
        skip = not rows
        subject = 'Critical Geo Intel Alert - %d item(s)' % len(rows)
    else:
        cats = _aggregate(articles, [{'$match': query}, {'$group': {'_id': '$category', 'cnt': {'$sum': 1}}}, {'$sort': {'cnt': -1}}, {'$limit': 101}], session, 100)
        countries = _aggregate(articles, [{'$match': {**query, 'country': {'$nin': [None, '']}}}, {'$group': {'_id': '$country', 'cnt': {'$sum': 1}}}, {'$sort': {'cnt': -1}}, {'$limit': 8}], session, 8)
        def stats(values, key):
            out = []
            for r in values:
                if type(r) is not dict or set(r) != {'_id', 'cnt'} or type(r['_id']) is not str or len(r['_id']) > 200 or type(r['cnt']) is not int or not 0 <= r['cnt'] <= 2**53:
                    raise ValueError('Bounded aggregate schema required')
                out.append({key: r['_id'], 'cnt': r['cnt']})
            return out
        cats, countries = stats(cats, 'category'), stats(countries, 'country')
        html = renderer('geo_weekly', {'weekly_top_articles': lambda **kw: rows,
               'category_counts': lambda **kw: cats, 'top_countries': lambda **kw: countries}, now=now)(days=7)
        subject = 'Geo Intel Weekly Summary - ' + now.strftime('%d %b %Y')
        skip = False
    html = sanitize_html(html)
    if len(html.encode()) > 1024 * 1024:
        raise ValueError('Mail output cap exceeded')
    return {'kind': kind, 'subject': subject, 'html': html, 'fetched_ids': fetched,
            'displayed_ids': displayed, 'mark_ids': [] if kind == 'weekly' or skip else fetched if policy == 'fetched' else displayed,
            'critical_count': critical, 'skip': skip, 'policy': policy,
            'source_scope': 'transaction_snapshot', 'clock_scope': 'UTC',
            'events_scope': 'queried_90day' if kind == 'digest' else 'not_in_original_report'}
