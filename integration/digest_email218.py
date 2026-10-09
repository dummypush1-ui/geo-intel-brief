"""Supplied candidate email only. No sender, DB, archive or receipt proof."""
VERSION = 'digest_email218_v1'
ALGORITHM = 'sha256_canonical_json_ascii'
COMBINED_CAP = 80 * 1024
HTML_CAP = 60 * 1024


def _fail():
    raise ValueError('Email candidate held') from None


def _bytes(subject, body, text):
    try:
        lengths = [len(v.encode('utf-8')) for v in (subject, body, text)]
    except Exception:
        _fail()
    if sum(lengths) > COMBINED_CAP or lengths[1] > HTML_CAP:
        _fail()
    return lengths


def _digest(candidate):
    import hashlib
    import json
    return hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def render_candidate(*, enabled=False, **args):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'send_allowed': False, 'ready': False, 'archive_proof': False}
    result = None
    try:
        result = _render(args)
    except Exception:
        pass
    if result is None:
        _fail()
    return result


def _render(args):
    import html
    import re
    from datetime import datetime, timezone, timedelta
    from bson import ObjectId
    from integration.digest_dates202 import select_normalized
    from integration.digest_render203 import plain, link
    fields = {'rows', 'now', 'date_field', 'displayed_receipts', 'offset_minutes', 'offset_label', 'limit'}
    if set(args) != fields:
        _fail()
    rows, now = args['rows'], args['now']
    if type(rows) is not list or len(rows) > 1000 or type(now) is not datetime or now.tzinfo is not timezone.utc:
        _fail()
    if type(args['date_field']) is not str or args['date_field'] not in ('published', 'created_at'):
        _fail()
    if type(args['limit']) is not int or not 1 <= args['limit'] <= 60:
        _fail()
    offset, label = args['offset_minutes'], args['offset_label']
    if type(offset) is not int or not -1439 <= offset <= 1439 or type(label) is not str:
        _fail()
    sign = '+' if offset >= 0 else '-'
    wanted = sign + f'{abs(offset)//60:02d}:{abs(offset)%60:02d}'
    if label != wanted or re.fullmatch(r'[+-][0-2][0-9]:[0-5][0-9]', label, re.ASCII) is None:
        _fail()
    receipts = args['displayed_receipts']
    if type(receipts) is not dict or set(receipts) != {'email', 'telegram', 'whatsapp'} or any(type(k) is not str for k in receipts):
        _fail()
    for ids in receipts.values():
        if type(ids) is not tuple or any(type(v) is not ObjectId for v in ids):
            _fail()
    for row in rows:
        if type(row) is not dict or any(type(k) is not str for k in row):
            _fail()
        for k, value in row.items():
            if k in ('published', 'created_at'):
                if type(value) not in (str, datetime):
                    _fail()
            elif k == '_id':
                if type(value) is not ObjectId:
                    _fail()
            elif k == 'emailed':
                if value is not None and type(value) is not bool:
                    _fail()
            elif k in ('score', 'corroboration'):
                if type(value) not in (int, float):
                    _fail()
            elif type(value) is not str:
                _fail()
        # Whole input URL validation matches203: refuse all, even excluded rows.
        link(row.get('url', ''))
    selection = select_normalized(rows, now, date_field=args['date_field'], channel='email',
                                  displayed_receipts=receipts, limit=args['limit'])
    union = sorted(str(v) for v in selection['displayed_union_ids'])
    if len(union) > 120 or len(union) != len(set(union)):
        _fail()
    if not union:
        return {'state': 'skipped_empty_candidate', 'skip': True, 'send_allowed': False,
                'ready': False, 'archive_proof': False}
    asof = now.isoformat(timespec='microseconds')
    shifted = now.astimezone(timezone(timedelta(minutes=offset))).isoformat(timespec='microseconds')
    subject = 'Geo Intel Brief - ' + asof + ' UTC'
    clean = lambda s: plain(s)
    escape = lambda s: html.escape(clean(s), quote=True)
    heading = 'Geo Intel Brief'
    introduction = 'Candidate only, not approved or sent. As of ' + shifted + ' (fixed offset ' + label + ').'
    body = ['<!doctype html><html><body style="margin:0;background:#f2f4f7;color:#243247;font-family:Arial,sans-serif"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="100%" cellpadding="16" cellspacing="0" style="max-width:680px;background:white"><tr><td><h1 style="font-size:24px">' + escape(heading) + '</h1><p style="font-size:14px;line-height:1.5">' + escape(introduction) + '</p></td></tr>']
    text = [heading, introduction]
    sections = []; rendered_html = []; rendered_text = []
    for name, title in (('last_24h', 'Last 24 hours'), ('last_7days', 'Last 7 days (includes last 24 hours)')):
        selected = selection['sections'][name]
        ids = [str(r['_id']) for r in selected['rows']]
        sections.append({'name': name, 'heading': title, 'ids': ids, 'eligible_count': selected['eligible_count'],
                         'omitted_count': selected['eligible_count'] - len(ids)})
        count = f'Showing {len(ids)} of {selected["eligible_count"]}'
        body.append('<tr><td><h2 style="font-size:20px">' + escape(title) + '</h2><p>' + escape(count) + '</p></td></tr>')
        text.extend([title, count])
        for row in selected['rows']:
            identity = str(row['_id'])
            title_text = clean(row['title']) or 'Untitled article'
            summary = clean(row['summary']); source = clean(row['source']); category = clean(row['category'])
            url = link(row['url']); meta = source + ' | ' + category + ' | score ' + str(row['score'])
            body.append('<tr><td data-article-id="' + identity + '" style="border-top:1px solid #dce2eb;overflow-wrap:anywhere"><p style="font-size:12px;color:#526178">' + escape(meta) + '</p><h3 style="font-size:17px;line-height:1.4"><a href="' + html.escape(url, quote=True) + '" style="color:#174b85">' + escape(title_text) + '</a></h3><p style="font-size:15px;line-height:1.5">' + escape(summary) + '</p></td></tr>')
            text.extend(['Article ID: ' + identity, clean(meta), title_text, summary, url])
            rendered_html.append(identity); rendered_text.append(identity)
    body.append('<tr><td><p style="font-size:12px;color:#526178">Supplied article candidate only. Events not supplied. Receipt membership and source completeness unverified.</p></td></tr></table></td></tr></table></body></html>')
    text.append('Supplied article candidate only. Events not supplied. Receipt membership and source completeness unverified.')
    if rendered_html != rendered_text or sorted(set(rendered_html)) != union:
        _fail()
    body = ''.join(body); text = '\n'.join(text)
    _bytes(subject, body, text)
    candidate = {'renderer_version': VERSION, 'digest_algorithm': ALGORITHM, 'kind': 'digest',
                 'date_field': args['date_field'], 'asof_utc': asof, 'offset_minutes': offset,
                 'offset_label': label, 'subject': subject, 'html': body, 'text': text,
                 'sections': sections, 'sorted_union_ids': union, 'skip': False}
    return {'state': 'supplied_email_candidate_only', 'send_allowed': False, 'ready': False,
            'archive_proof': False, 'candidate': candidate, 'content_digest': _digest(candidate)}
