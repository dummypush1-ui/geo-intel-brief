# Copyright (c) 2026 Push. All rights reserved.
"""Original geonews reports, prepared for the Apps Script delivery path only.

No client, sender, callback, environment read, marking, scheduler or live route.
Supplied rows are a bounded sample, not a verified unsent queue or full weekly
archive. Returned IDs are diagnostic only and cannot authorize marking.
"""
from collections import Counter
from datetime import datetime, timezone, timedelta, date
from hashlib import sha256
import json
import ipaddress
import math
import re
import socket
from urllib.parse import urlsplit
from integration.renderer_scope import renderer
from integration.html_safety import sanitize_html

ARTICLE_FIELDS = ('_id', 'title', 'summary', 'url', 'source', 'category',
                  'country', 'risk_level', 'score', 'credibility',
                  'corroboration', 'published', 'created_at', 'emailed')
EVENT_FIELDS = ('name', 'event_date', 'source_url', 'category', 'confidence', 'description')
MAX_ROWS = 200
MAX_BYTES = 512 * 1024


def _clock(now):
    if type(now) is not datetime or type(now.tzinfo) is not timezone:
        raise ValueError('Fixed aware clock required')
    now = now.astimezone(timezone.utc)
    if not 2000 <= now.year <= 2090:
        raise ValueError('Clock outside supported window')
    return now


def _stamp(value):
    if type(value) is not str:
        raise ValueError('Zoned timestamp required')
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None or not 1970 <= stamp.year <= 2100:
            raise ValueError()
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError('Zoned timestamp required') from None


def _url(value):
    if not value:
        return ''
    try:
        u = urlsplit(value)
        if (u.scheme != 'https' or not u.hostname or u.username or u.password
                or u.query or u.fragment or u.port not in (None, 443)
                or any(c.isspace() or ord(c) < 32 for c in value)):
            raise ValueError()
        host = u.hostname.casefold()
        if (host == 'localhost' or '.' not in host or host.endswith('.')
                or host.endswith(('.internal', '.localhost', '.local', '.invalid', '.test'))
                or re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*', host)):
            raise ValueError()
        # No DNS lookup: inet_aton detects browser-compatible legacy IPv4 spelling.
        try:
            socket.inet_aton(host)
        except OSError:
            pass
        else:
            raise ValueError()
        try:
            address = ipaddress.ip_address(u.hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError()
        return value
    except ValueError:
        raise ValueError('Public HTTPS link without query required') from None


def _snapshot(articles, events):
    if type(articles) is not list or type(events) is not list:
        raise ValueError('Plain lists required')
    if len(articles) > MAX_ROWS or len(events) > MAX_ROWS:
        raise ValueError('Snapshot row cap exceeded')
    budget = 0
    results = []
    for rows, fields in ((articles, ARTICLE_FIELDS), (events, EVENT_FIELDS)):
        clean = []
        identities = set()
        for row in rows:
            if type(row) is not dict or any(type(k) is not str or k not in fields for k in row):
                raise ValueError('Closed plain row required')
            item = {}
            for k in fields:
                v = row.get(k, False if k == 'emailed' else 1 if k == 'corroboration'
                            else 0 if k == 'score' else '')
                if k == 'emailed':
                    if type(v) is not bool:
                        raise ValueError('Boolean emailed required')
                elif k in ('score', 'corroboration'):
                    if type(v) not in (int, float) or not 0 <= v <= 1000000 or not math.isfinite(v):
                        raise ValueError('Finite bounded number required')
                elif (type(v) is not str or len(v) > 16000
                      or any(0xD800 <= ord(c) <= 0xDFFF or ord(c) < 32 and c not in '\n\t' for c in v)):
                    raise ValueError('Bounded text required')
                item[k] = v
            if fields == ARTICLE_FIELDS:
                if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}', item['_id']) or item['_id'] in identities:
                    raise ValueError('Unique opaque fixture ID required')
                identities.add(item['_id'])
                if not item['title'].strip() or not item['url']:
                    raise ValueError('Title and URL required')
                _stamp(item['published'])
                _stamp(item['created_at'])
                item['url'] = _url(item['url'])
            else:
                try:
                    d = date.fromisoformat(item['event_date'])
                    if not item['name'].strip() or d.isoformat() != item['event_date']:
                        raise ValueError()
                except ValueError:
                    raise ValueError('Event name and ISO date required') from None
                item['source_url'] = _url(item['source_url'])
            budget += len(json.dumps(item, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
            if budget > MAX_BYTES:
                raise ValueError('Snapshot byte cap exceeded')
            clean.append(item)
        results.append(clean)
    return results


def prepare_report(kind, articles, events, now):
    """Pure Apps Script-shaped *diagnostic*, with original renderer definitions.

    Critical: >= now-6h, score DESC. Weekly: >= now-7d, top20, country top8.
    Digest: fetched top60 before score4 display filter, plus UTC90day events.
    Preserves fetched/displayed distinction, never resolves marking policy.
    Events are only in the original digest, not invented into critical/weekly.
    """
    if type(kind) is not str or kind not in ('digest', 'critical', 'weekly'):
        raise ValueError('Unknown report kind')
    now = _clock(now)
    rows, event_rows = _snapshot(articles, events)
    if kind != 'digest' and event_rows:
        raise ValueError('Original critical/weekly reports do not contain events')
    refs = []
    critical = 0
    shown = 0
    if kind == 'critical':
        selected = sorted((r for r in rows if r['risk_level'] == 'CRITICAL'
                           and _stamp(r['created_at']) >= now - timedelta(hours=6)),
                          key=lambda r: r['score'], reverse=True)
        critical = shown = len(selected)
        body = renderer('geo_critical', {}, now=now)(selected) if selected else ''
        subject = 'Critical Geo Intel Alert - %d item(s)' % critical
        refs = [r['_id'] for r in selected]
        skip = not selected
    elif kind == 'weekly':
        selected = [r for r in rows if _stamp(r['created_at']) >= now - timedelta(days=7)]
        top = sorted(selected, key=lambda r: r['score'], reverse=True)[:20]
        cats = Counter(r['category'] for r in selected)
        countries = Counter(r['country'] for r in selected if r['country'])
        deps = {
            'weekly_top_articles': lambda **kw: top,
            'category_counts': lambda **kw: [{'category': k, 'cnt': v} for k, v in cats.most_common()],
            'top_countries': lambda **kw: [{'country': k, 'cnt': v} for k, v in countries.most_common(8)],
        }
        body = renderer('geo_weekly', deps, now=now)(days=7)
        subject = 'Geo Intel Weekly Summary - ' + now.strftime('%d %b %Y')
        shown = len(top)
        skip = False
    else:
        selected = sorted((r for r in rows if not r['emailed']),
                          key=lambda r: (r['score'], _stamp(r['published'])), reverse=True)[:60]
        today = now.date()
        upcoming = sorted((e for e in event_rows if today <= date.fromisoformat(e['event_date'])
                           <= today + timedelta(days=90)), key=lambda e: e['event_date'])
        body, critical, refs = renderer('geo_digest', {
            'unemailed_articles': lambda: selected,
            'upcoming_events': lambda days: upcoming,
        }, now=now)()
        shown = sum(r['score'] >= 4 for r in selected)
        subject = 'Geo Intel Brief - ' + now.strftime('%d %b %Y %H:%M UTC')
        skip = not refs and not critical
    notice = '<p>Supplied sample only. UTC clock. Not a verified unsent queue or full weekly archive. Delivery and marking are off.</p>'
    # Insert into body instead of wrapping a nested HTML document.
    index = body.find('>', body.find('<body')) if '<body' in body else -1
    body = body[:index + 1] + notice + body[index + 1:] if index >= 0 else notice + body
    body = sanitize_html(body)
    if any(re.search(r'(?<![A-Za-z0-9_.:-])' + re.escape(r['_id']) + r'(?![A-Za-z0-9_.:-])', body, re.I) for r in rows if len(r['_id']) >= 8):
        raise ValueError('Diagnostic ID in rendered output')
    if len(body.encode('utf-8')) > MAX_BYTES * 2:
        raise ValueError('Output byte cap exceeded')
    return {'kind': kind, 'subject': subject, 'html': body, 'critical_count': critical,
            'fetched_sample_count': len(selected), 'displayed_sample_count': shown,
            'diagnostic_ids': list(refs), 'skip': skip, 'delivery_path': 'apps_script',
            'scope': 'supplied_sample_not_delivery_payload', 'clock_scope': 'fixed_UTC',
            'marking_policy': 'unresolved_fetched_vs_displayed',
            'identity_scan': 'whole_token_min8_not_complete_secret_detection',
            'snapshot_hash': sha256(json.dumps({'articles': rows, 'events': event_rows},
                sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(),
            'network': False, 'delivery': False, 'writes': False}
