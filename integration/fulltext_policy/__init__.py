"""Default-OFF fulltext transport preparation. No fetch/extractor/send clients.

Exact article URLs must be installation-reviewed, never learned from feed data.
DNS/peer here are supplied evidence, not network proof. No extractor fallback.
"""
from urllib.parse import urlsplit
from collector113_prep.transport_policy import endpoint_plan, decode_response, TransportRefused
import hashlib

class FulltextHeld(ValueError):
    pass


def _feeds(reviewed_urls):
    if type(reviewed_urls) is not tuple or not 1 <= len(reviewed_urls) <= 64:
        raise FulltextHeld('Exact installed article URL policy required')
    if len(set(reviewed_urls)) != len(reviewed_urls):
        raise FulltextHeld('Duplicate installed URL')
    feeds = []
    for url in reviewed_urls:
        if type(url) is not str or not 1 <= len(url) <= 2000 or not url.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in url) or '\\' in url:
            raise FulltextHeld('Article URL grammar')
        try:
            p = urlsplit(url)
            if p.scheme != 'https' or not p.hostname or '.' not in p.hostname or p.username is not None or p.password is not None or p.fragment or p.port not in (None, 443):
                raise FulltextHeld('Article origin policy')
        except ValueError:
            raise FulltextHeld('Article origin policy') from None
        feeds.append(('Reviewed article', url, 'MEDIUM'))
    return tuple(feeds)


def plan(reviewed_urls, url, answers, peer, *, enabled=False):
    if type(enabled) is not bool:
        raise FulltextHeld('Exact feature switch required')
    if not enabled:
        return {'state': 'disabled', 'network': False, 'extraction': False, 'production_ready': False}
    try:
        endpoint = endpoint_plan(_feeds(reviewed_urls), url, answers, peer)
    except (TransportRefused, ValueError, TypeError):
        raise FulltextHeld('Fulltext endpoint refused') from None
    return {'state': 'supplied_endpoint_plan_only', 'endpoint': endpoint,
            'network': False, 'extraction': False, 'production_ready': False,
            'pending': ['actual_pinned_peer_tls_fetch', 'isolated_pinned_extractor', 'whole_fetch_extract_supervision']}


def prepare_body(reviewed_urls, url, answers, peer, status, headers, chunks, *, deadline, clock, enabled=False):
    result = plan(reviewed_urls, url, answers, peer, enabled=enabled)
    if not enabled:
        return result
    try:
        body = decode_response(status, headers, chunks, deadline=deadline, clock=clock)
    except (TransportRefused, ValueError, TypeError):
        raise FulltextHeld('Fulltext supplied body refused') from None
    # No character decoding here. HTML bytes remain unparsed untrusted input.
    return dict(result, bytes=body['bytes'], input_sha256=hashlib.sha256(body['bytes']).hexdigest(),
                wire_bytes=body['wire_bytes'], decoded_bytes=body['decoded_bytes'],
                state='supplied_bytes_pending_isolated_extractor')
