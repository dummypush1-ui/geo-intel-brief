# Copyright (c) 2026 Push. All rights reserved.
"""Bounded CSV/JSON import and injected pulls. No network/client at import time.

There is deliberately no guessed NDAP API. A reviewed export URL or an OGD
resource ID is required. Credentials never enter provenance or error results.
"""
from copy import deepcopy
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import re
from urllib.parse import urlsplit

MAX_BYTES = 5_000_000
MAX_ROWS = 10_000
MAX_TOTAL_BYTES = 10_000_000
MAX_COLUMNS = 100
MISSING = {'', 'na', 'n/a', 'null', 'none', '..', '-', '—'}


def text(value, limit=300):
    if type(value) is not str or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid bounded text')
    return value.strip()


def iso_date(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('ISO dataset date required')
    date.fromisoformat(value)
    return value


def https_url(value):
    value = text(value, 2048)
    u = urlsplit(value)
    if (u.scheme != 'https' or not u.hostname or u.username is not None or
            u.password is not None or u.fragment or u.query or u.port not in (None, 443)
            or '\\' in value or any(c.isspace() for c in value)):
        raise ValueError('Credential-free HTTPS source URL required')
    host = u.hostname.lower()
    if not host.endswith(('.gov.in', '.nic.in')):
        raise ValueError('Official government source required')
    return value


def source_spec(*, dataset_id, publisher, source_url, provider, dataset_date,
                coverage, columns, license_url, reuse_reviewed=False):
    """Dataset-specific semantic mapping, not name-based fuzzy guesses.

    Columns maps canonical names to exact supplied headers. Metric, value and
    unit are mandatory. Geography is kept as published; no guessed LGD codes.
    """
    if not re.fullmatch(r'[a-z][a-z0-9_-]{2,79}', text(dataset_id, 80)):
        raise ValueError('Dataset identity required')
    if provider not in ('ndap_export', 'ogd'):
        raise ValueError('Explicit supported provider required')
    if type(reuse_reviewed) is not bool:
        raise ValueError('Boolean reuse review required')
    if type(columns) is not dict or not {'metric', 'value', 'unit'} <= set(columns):
        raise ValueError('Exact metric/value/unit header mapping required')
    allowed = {'metric', 'value', 'unit', 'state', 'district', 'state_code',
               'district_code', 'period', 'source_row_id'}
    if set(columns) - allowed or len(set(columns.values())) != len(columns):
        raise ValueError('Unique known canonical column mapping required')
    columns = {k: text(v, 120) for k, v in columns.items()}
    if not all(columns.values()):
        raise ValueError('Nonempty column mapping required')
    return {'dataset_id': dataset_id, 'publisher': text(publisher),
            'source_url': https_url(source_url), 'provider': provider,
            'dataset_date': None if dataset_date is None else iso_date(dataset_date),
            'coverage': text(coverage), 'columns': columns,
            'license_url': https_url(license_url), 'reuse_reviewed': reuse_reviewed}


def checked_spec(spec):
    if type(spec) is not dict:
        raise ValueError('Plain source specification required')
    return source_spec(**spec)


def parse_export(payload, format):
    if type(payload) is not bytes or not payload or len(payload) > MAX_BYTES:
        raise ValueError('Bounded nonempty export required')
    raw = payload.decode('utf-8-sig', errors='strict')
    if format == 'csv':
        reader = csv.DictReader(io.StringIO(raw, newline=''))
        names = reader.fieldnames
        if not names or len(names) > MAX_COLUMNS or len(set(names)) != len(names):
            raise ValueError('Unique bounded CSV headers required')
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('CSV row width mismatch')
            rows.append(row)
            if len(rows) > MAX_ROWS:
                raise ValueError('Export row bound exceeded')
    elif format == 'json':
        rows = json.loads(raw)
        if type(rows) is dict and set(rows) == {'records'}:
            rows = rows['records']
    else:
        raise ValueError('Only explicit CSV or JSON exports supported')
    return validate_rows(rows)


def validate_rows(rows):
    if type(rows) is not list or not rows or len(rows) > MAX_ROWS:
        raise ValueError('Bounded nonempty row list required')
    for row in rows:
        if type(row) is not dict or not row or len(row) > MAX_COLUMNS:
            raise ValueError('Bounded plain row required')
        for key, value in row.items():
            text(key, 120)
            if type(value) not in (str, int, float, type(None)):
                raise ValueError('Scalar row values required')
            if type(value) is str and len(value) > 4000:
                raise ValueError('Row text too long')
    return rows


def number(value):
    if value is None or (type(value) is str and value.strip().casefold() in MISSING):
        return None
    if type(value) is bool:
        raise ValueError('Boolean not numeric')
    try:
        # No automatic thousands separator, percent, currency or unit stripping.
        n = Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError('Invalid numeric observation') from None
    if not n.is_finite() or n.adjusted() > 100 or n.as_tuple().exponent < -100 or len(n.as_tuple().digits) > 200:
        raise ValueError('Finite bounded numeric observation required')
    return format(n, 'f') if n != 0 else '0'


def scalar(value, limit=300):
    if value is None:
        return None
    return text(str(value), limit) or None


def normalize(rows, spec, payload_sha256):
    spec = checked_spec(spec)
    validate_rows(rows)
    if not re.fullmatch(r'[0-9a-f]{64}', payload_sha256):
        raise ValueError('Source payload hash required')
    c = spec['columns']
    out, identities = [], set()
    for row in rows:
        if set(c.values()) - set(row):
            raise ValueError('Mapped source header missing')
        get = lambda key: scalar(row[c[key]]) if key in c else None
        metric, unit = get('metric'), get('unit')
        if not metric or not unit:
            raise ValueError('Metric and published unit required')
        location = {k: get(k) for k in ('state', 'district', 'state_code', 'district_code')}
        identity = {'dataset_id': spec['dataset_id'], 'metric': metric, 'unit': unit,
                    'period': get('period'), 'geography': location,
                    'source_row_id': get('source_row_id')}
        rid = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False,
                                        separators=(',', ':')).encode()).hexdigest()
        if rid in identities:
            raise ValueError('Duplicate or ambiguous observation identity')
        identities.add(rid)
        value = number(row[c['value']])
        out.append({'_id': rid, **identity, 'value_decimal': value,
                    'value_state': 'missing' if value is None else 'published',
                    'dataset_date': spec['dataset_date'],
                    'freshness': 'unknown' if spec['dataset_date'] is None else 'dated_snapshot',
                    'source_url': spec['source_url'], 'publisher': spec['publisher'],
                    'provider': spec['provider'], 'coverage': spec['coverage'],
                    'license_url': spec['license_url'], 'reuse_reviewed': spec['reuse_reviewed'],
                    'payload_sha256': payload_sha256})
    return out


def import_export(payload, format, spec):
    digest = hashlib.sha256(payload).hexdigest() if type(payload) is bytes else ''
    return normalize(parse_export(payload, format), spec, digest)


def pull_export(spec, export_url, format, transport, *, enabled=False):
    """Injected transport must enforce DNS, no redirects, TLS and byte/time caps.

    transport(url, params, max_bytes, timeout_seconds) returns bytes. No retry,
    caller exception disclosure, account creation or import-time networking.
    """
    spec = checked_spec(spec)
    if enabled is not True:
        return {'state': 'disabled', 'records': [], 'error': None}
    if not spec['reuse_reviewed']:
        return {'state': 'held', 'records': [], 'error': 'reuse_review_required'}
    export_url = https_url(export_url)
    if urlsplit(export_url).hostname != urlsplit(spec['source_url']).hostname:
        raise ValueError('Export must match reviewed source host')
    try:
        body = transport(export_url, {}, MAX_BYTES, 20)
        records = import_export(body, format, spec)
    except Exception:
        return {'state': 'failed', 'records': [], 'error': 'export_pull_or_validation_failed'}
    return {'state': 'complete', 'records': records, 'error': None}


def metadata_int(value):
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and re.fullmatch(r'0|[1-9][0-9]{0,7}', value):
        return int(value)
    raise ValueError('Exact nonnegative integer metadata required')


def pull_ogd(spec, resource_id, api_key, transport, *, enabled=False,
             page_size=100, max_pages=100):
    """API template used by OGD clients; actual dataset ID/schema must be reviewed.

    Complete only on consistent total/count/offset and exact bounded coverage.
    Any partial/error preserves caller's old snapshot. No production writes.
    """
    spec = checked_spec(spec)
    if enabled is not True:
        return {'state': 'disabled', 'records': [], 'error': None}
    if not spec['reuse_reviewed']:
        return {'state': 'held', 'records': [], 'error': 'reuse_review_required'}
    if spec['provider'] != 'ogd' or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', resource_id):
        raise ValueError('Reviewed OGD UUID required')
    if type(api_key) is not str or not api_key or len(api_key) > 200:
        raise ValueError('Server-only API key required')
    if type(page_size) is not int or not 1 <= page_size <= 100 or type(max_pages) is not int or not 1 <= max_pages <= 100:
        raise ValueError('Bounded pagination required')
    rows, total, page_hashes = [], None, set()
    total_bytes = 0
    digest = hashlib.sha256()
    try:
        for _ in range(max_pages):
            offset = len(rows)
            body = transport('https://api.data.gov.in/resource/' + resource_id,
                             {'api-key': api_key, 'format': 'json', 'offset': offset,
                              'limit': page_size}, MAX_BYTES, 20)
            if type(body) is not bytes or not body or len(body) > MAX_BYTES:
                raise ValueError('Invalid API page')
            total_bytes += len(body)
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError('Aggregate response byte cap exceeded')
            page = json.loads(body.decode('utf-8-sig'))
            if type(page) is not dict or str(page.get('status')).casefold() not in ('ok', 'success'):
                raise ValueError('API unsuccessful')
            page_total = metadata_int(page.get('total'))
            # Exact integer metadata avoids coercion/truncation of malformed totals.
            if type(page_total) is not int or not 1 <= page_total <= MAX_ROWS:
                raise ValueError('Valid complete dataset total required')
            if total is None:
                total = page_total
            if total != page_total or metadata_int(page.get('offset')) != offset:
                raise ValueError('Changed dataset or offset mismatch')
            items = validate_rows(page.get('records'))
            if len(items) > page_size or metadata_int(page.get('count')) != len(items):
                raise ValueError('Count mismatch')
            page_hash = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).digest()
            if page_hash in page_hashes:
                raise ValueError('Repeated page')
            page_hashes.add(page_hash)
            rows.extend(items)
            digest.update(len(body).to_bytes(8, 'big')); digest.update(body)
            if len(rows) > total:
                raise ValueError('Total mismatch')
            if len(rows) == total:
                records = normalize(rows, spec, digest.hexdigest())
                return {'state': 'complete', 'records': records, 'error': None}
        return {'state': 'partial', 'records': [], 'error': 'page_limit_reached'}
    except Exception:
        return {'state': 'failed', 'records': [], 'error': 'api_pull_or_validation_failed'}


def stage_snapshot(result, current, dataset_id, captured_at):
    """Pure atomic candidate for a new isolated dataset layer, not articles.

    Returns a deep copy only after complete validation. Caller must use its own
    reviewed transactional persistence; no clients/collections/TTL are touched.
    """
    if type(current) is not dict or type(result) is not dict:
        raise ValueError('Plain snapshot inputs required')
    if result.get('state') != 'complete':
        return deepcopy(current)
    rows = result.get('records')
    if type(rows) is not list or not rows or any(type(r) is not dict or r.get('dataset_id') != dataset_id for r in rows):
        raise ValueError('Complete matching dataset required')
    dt = datetime.fromisoformat(captured_at)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('Timezone-aware capture time required')
    candidate = deepcopy(current)
    candidate[dataset_id] = {'captured_at': dt.astimezone(timezone.utc).isoformat(),
                             'records': deepcopy(rows), 'state': 'complete'}
    return candidate
