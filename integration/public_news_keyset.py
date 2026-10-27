"""Stateless, signed public-news continuation pages for multi-worker deployments.

Each request opens and closes its own bounded Mongo cursor. The continuation
token contains only a scan offset, expiry, page limit, and filter digest; it is
authenticated with a key derived from the shared Mongo URI, never the URI itself.
Reads remain mutable rather than a stable snapshot.
"""
import base64
import hashlib
import hmac
import json
import re
import struct
import time
from threading import BoundedSemaphore

from integration.loaded_news import selection
from integration.news_pages import PageBusy, PageExpired, PageUnavailable, validate
from integration.news_view import normalize_row
from integration.public_news import READ_STORE_FIELDS, public_news_row

VERSION = 1
SCAN_BUDGET = 1000
MAX_SOURCE_OFFSET = 10_000_000
TOKEN_TTL_SECONDS = 1800
TOKEN_MAC_BYTES = 12
TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9_-]{43}$')
SORTS = {
    'newest': [('created_at', -1), ('_id', -1)],
    'title': [('title', 1), ('_id', 1)],
    'country': [('country', 1), ('_id', 1)],
    'score': [('score', -1), ('_id', -1)],
}


def _secret(uri):
    if type(uri) is not str or not uri:
        raise ValueError('Shared Mongo URI required for public cursor signing')
    return hashlib.sha256(b'geo-intel-public-news-cursor-v1\0' + uri.encode('utf-8')).digest()


def _filter_digest(filters, limit):
    canonical = json.dumps(
        {'filters': filters, 'limit': limit},
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(canonical).digest()[:10]


def _encode(secret, offset, expiry, filters, limit):
    if not 0 <= offset <= MAX_SOURCE_OFFSET:
        raise PageExpired()
    payload = struct.pack('>B I I B', VERSION, offset, expiry, limit) + _filter_digest(filters, limit)
    signature = hmac.new(secret, payload, hashlib.sha256).digest()[:TOKEN_MAC_BYTES]
    return base64.urlsafe_b64encode(payload + signature).decode('ascii').rstrip('=')


def _decode(secret, token, filters, limit, now):
    if type(token) is not str or not TOKEN_PATTERN.fullmatch(token):
        raise PageExpired()
    try:
        raw = base64.urlsafe_b64decode(token + '=')
    except Exception:
        raise PageExpired() from None
    payload, signature = raw[:-TOKEN_MAC_BYTES], raw[-TOKEN_MAC_BYTES:]
    expected = hmac.new(secret, payload, hashlib.sha256).digest()[:TOKEN_MAC_BYTES]
    if len(payload) != 20 or not hmac.compare_digest(signature, expected):
        raise PageExpired()
    version, offset, expiry, token_limit = struct.unpack('>B I I B', payload[:10])
    if (
        version != VERSION
        or token_limit != limit
        or offset > MAX_SOURCE_OFFSET
        or expiry <= now
        or expiry > now + TOKEN_TTL_SECONDS + 60
        or not hmac.compare_digest(payload[10:], _filter_digest(filters, limit))
    ):
        raise PageExpired()
    return offset, expiry


def _page(pages, secret, slots, filters, limit=25, token=''):
    validate(filters, limit, token)
    if pages.stopped.is_set():
        raise PageUnavailable()
    if not slots.acquire(blocking=False):
        raise PageBusy()
    cursor = None
    try:
        now = int(time.time())
        if token:
            source_offset, expiry = _decode(secret, token, filters, limit, now)
        else:
            source_offset, expiry = 0, now + TOKEN_TTL_SECONDS
        if source_offset > MAX_SOURCE_OFFSET - SCAN_BUDGET:
            raise PageExpired()
        try:
            cursor = pages.store.find({}, {key: 1 for key in READ_STORE_FIELDS})
            cursor.sort(SORTS[filters['sort']])
            cursor.skip(source_offset)
            cursor.limit(SCAN_BUDGET)
            cursor.batch_size(100)
            cursor.max_time_ms(2000)
        except Exception:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            raise PageUnavailable() from None

        items = []
        scanned = 0
        exhausted = False
        try:
            while len(items) < limit and scanned < SCAN_BUDGET:
                try:
                    raw = next(cursor)
                except StopIteration:
                    exhausted = True
                    break
                scanned += 1
                clean = pages.sanitize([raw])
                if not clean:
                    continue
                row = normalize_row(clean[0], 'geo')
                if row is None:
                    continue
                chosen = selection([row], **filters)['items']
                if chosen:
                    items.append(public_news_row(chosen[0]))
        except Exception:
            raise PageUnavailable() from None

        next_offset = source_offset + scanned
        next_token = None if exhausted else _encode(secret, next_offset, expiry, filters, limit)
        return {
            'items': items,
            'scope': 'whole_geo_store_cursor',
            'consistency': 'mutable_read_not_snapshot',
            'sort_semantics': 'raw_mongo_source_fields_with_id_tiebreak',
            'limit': limit,
            'offset': source_offset,
            'next_cursor': next_token,
            'exhausted': exhausted,
            'scanned_this_page': scanned,
            'total_count': None,
        }
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        slots.release()


def install(app, mongo_uri):
    """Replace the public page method with cross-worker stateless paging."""
    from integration.news_pages import WholeGeoPages

    pages = app.extensions.get('whole_news_pages')
    if type(pages) is not WholeGeoPages:
        raise ValueError('Verified whole-store pages required')
    if app.extensions.get('public_news_cursor_mode') is not None:
        raise ValueError('Public news cursor mode already installed')
    secret = _secret(mongo_uri)
    slots = BoundedSemaphore(8)

    def page(filters, limit=25, token=''):
        return _page(pages, secret, slots, filters, limit, token)

    pages.page = page
    app.extensions['public_news_cursor_mode'] = 'signed_stateless_offset_v1'
