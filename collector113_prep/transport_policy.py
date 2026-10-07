"""Inactive supplied-response streaming policy. No sockets or HTTP client.
DNS answers and peer are supplied test evidence, NOT real resolution/TLS proof.
A future connector must pin the validated address, check its actual peer, retain
TLS SNI/certificate verification, and enforce interruptible DNS/connect/read
wall deadlines. Checks here cannot interrupt a blocked iterator or resolver.
"""
import ipaddress
import math
import re
import time
import zlib
from urllib.parse import urlsplit
from collector109_prep.fetch_stage import _valid_feeds

MAX_WIRE = 1048576
MAX_DECODED = 1048576
MAX_CHUNK = 65536
MAX_CHUNKS = 4096
class TransportRefused(ValueError):
    pass

def _address(value):
    if type(value) is not str or len(value) > 64 or '%' in value:
        raise TransportRefused('Address shape')
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        raise TransportRefused('Literal address required') from None
    # Python 3.10 global includes some multicast; reject each category too.
    if (not ip.is_global or ip.is_multicast or ip.is_unspecified or
            ip.is_loopback or ip.is_link_local or ip.is_reserved or
            getattr(ip, 'ipv4_mapped', None) is not None or
            getattr(ip, 'sixtofour', None) is not None or
            getattr(ip, 'teredo', None) is not None):
        raise TransportRefused('Public unicast address required')
    # Deprecated 6to4 relay anycast is global in Python3.10 but not an
    # acceptable collector endpoint. Deny the full historical relay prefix.
    if ip.version == 4 and ip in ipaddress.ip_network('192.88.99.0/24'):
        raise TransportRefused('Deprecated relay anycast refused')
    # IPv6 translation ranges require explicit deployment policy, not a guess.
    if ip.version == 6 and (ip in ipaddress.ip_network('64:ff9b::/96') or
                           ip in ipaddress.ip_network('64:ff9b:1::/48')):
        raise TransportRefused('Translated address refused')
    return str(ip)

def endpoint_plan(feeds, url, answers, peer):
    """Offline plan over installed feed allowlist and supplied DNS/peer data."""
    _valid_feeds(feeds)
    if type(url) is not str or url not in {f[1] for f in feeds}:
        raise TransportRefused('URL not allowlisted')
    parts = urlsplit(url)
    if (parts.username or parts.password or parts.fragment or
            parts.port not in (None, 443) or not parts.hostname or
            not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', parts.hostname)):
        raise TransportRefused('HTTPS origin policy')
    if (type(answers) is not tuple or not 1 <= len(answers) <= 16):
        raise TransportRefused('Bounded DNS evidence required')
    addresses = tuple(_address(a) for a in answers)
    actual = _address(peer)
    if actual not in addresses:
        raise TransportRefused('Peer differs from reviewed DNS set')
    return {'hostname': parts.hostname, 'port': 443, 'pinned_address': actual,
            'request_target': parts.path + ('?' + parts.query if parts.query else ''),
            'tls_server_name': parts.hostname, 'redirects': False,
            'network_proof': False}

def decode_response(status, headers, chunks, *, deadline, clock=time.monotonic):
    """Decode bounded *raw compressed* chunks, never auto-decoded HTTP content.
Caller-supplied chunks are an offline test seam. Length describes wire bytes.
Reject redirects, stacked/unknown encodings, truncated/concatenated streams,
excess output, declared-length mismatches and all output after the deadline.
"""
    if type(status) is not int or status != 200:
        raise TransportRefused('HTTP status or redirect refused')
    if (type(headers) is not dict or len(headers) > 32 or
            type(deadline) not in (int, float) or not math.isfinite(deadline)):
        raise TransportRefused('Response shape')
    clean = {}
    for k, v in headers.items():
        if (type(k) is not str or type(v) is not str or not 1 <= len(k) <= 100 or
                len(v) > 2000 or '\r' in v or '\n' in v or
                not re.fullmatch(r'[A-Za-z0-9-]+', k)):
            raise TransportRefused('Header shape')
        key = k.lower()
        if key in clean:
            raise TransportRefused('Duplicate header')
        clean[key] = v.strip()
    encoding = clean.get('content-encoding', 'identity').lower()
    if encoding not in ('identity', 'gzip', 'deflate'):
        raise TransportRefused('Content encoding')
    length = clean.get('content-length')
    if length is not None:
        if not re.fullmatch(r'[0-9]{1,8}', length) or int(length) > MAX_WIRE:
            raise TransportRefused('Declared wire length')
        length = int(length)
    if 'transfer-encoding' in clean:
        # Real HTTP framing must be owned by the final connector. No ambiguous
        # TE/CL acceptance in this supplied-body stage.
        raise TransportRefused('Transfer framing not established')
    if type(chunks) not in (tuple, list) or len(chunks) > MAX_CHUNKS:
        raise TransportRefused('Bounded supplied chunk list required')
    def tick():
        now = clock()
        if type(now) not in (int, float) or not math.isfinite(now) or now >= deadline:
            raise TransportRefused('Response wall budget')
    decoder = None if encoding == 'identity' else zlib.decompressobj(31 if encoding == 'gzip' else 15)
    output = bytearray()
    wire = 0
    tick()
    try:
        for chunk in chunks:
            tick()
            if type(chunk) is not bytes or len(chunk) > MAX_CHUNK:
                raise TransportRefused('Raw chunk shape')
            wire += len(chunk)
            if wire > MAX_WIRE:
                raise TransportRefused('Wire budget')
            allowance = MAX_DECODED - len(output)
            data = chunk if decoder is None else decoder.decompress(chunk, allowance + 1)
            if len(data) > allowance:
                raise TransportRefused('Decoded budget')
            output.extend(data)
            if decoder is not None and (decoder.unconsumed_tail or decoder.unused_data):
                raise TransportRefused('Excess or concatenated compressed stream')
        if decoder is not None and not decoder.eof:
            raise TransportRefused('Truncated compressed stream')
    except zlib.error:
        raise TransportRefused('Malformed compression') from None
    tick()
    if length is not None and length != wire:
        raise TransportRefused('Wire length mismatch')
    if not output:
        raise TransportRefused('Empty response')
    return {'bytes': bytes(output), 'wire_bytes': wire, 'decoded_bytes': len(output),
            'encoding': encoding, 'network': False, 'delivery': False}
