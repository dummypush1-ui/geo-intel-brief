# Copyright (c) 2026 Push. All rights reserved.
"""Opt-in standard-library HTTPS GET transport with public DNS address pinning.

No cookies, redirects, retries, proxy-env usage, credentials on other hosts,
logs, cloud SDKs or import-time network. TLS verifies original DNS hostname.
"""
import http.client
import ipaddress
import socket
import re
import ssl
from urllib.parse import urlencode, urlsplit
from .core import https_url, MAX_BYTES


class PullError(Exception):
    """Sanitized failure; never exposes credential-bearing request paths."""


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address, timeout):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def government_get(url, params, max_bytes=MAX_BYTES, timeout_seconds=20):
    """Requires explicit call, accepts only official URLs and exact OGD params.

    Fixed original-host DNS, public-address validation and socket pinning avoid
    DNS rebinding between validation and connection. A timeout bounds socket
    operations, not total wall time; callers should also bound worker runtime.
    """
    url = https_url(url)
    u = urlsplit(url)
    if type(params) is not dict:
        raise ValueError('Plain request parameters required')
    if params:
        if (u.hostname != 'api.data.gov.in' or not re.fullmatch(r'/resource/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', u.path)
                or set(params) != {'api-key', 'format', 'offset', 'limit'}):
            raise ValueError('OGD-only closed query parameters required')
        if (type(params['api-key']) is not str or not 1 <= len(params['api-key']) <= 200
                or any(ord(c) < 32 for c in params['api-key']) or params['format'] != 'json'
                or type(params['offset']) is not int or not 0 <= params['offset'] <= 10_000
                or type(params['limit']) is not int or not 1 <= params['limit'] <= 100):
            raise ValueError('Bounded OGD query required')
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES or type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
        raise ValueError('Bounded request required')
    conn = None
    try:
        answers = socket.getaddrinfo(u.hostname, 443, type=socket.SOCK_STREAM)
        addresses = {a[4][0] for a in answers}
        if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
            raise PullError('Public addresses required')
        conn = _PinnedHTTPS(u.hostname, sorted(addresses)[0], timeout_seconds)
        target = (u.path or '/') + ('?' + urlencode(params) if params else '')
        conn.request('GET', target, headers={'Accept': 'application/json,text/csv',
                     'Accept-Encoding': 'identity', 'User-Agent': 'GeoIntelGovernmentData/1.0'})
        response = conn.getresponse()
        if response.status != 200:
            # Includes redirect, 401/403, quota/429 and challenges. No retries.
            raise PullError('Request not successful')
        if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
            raise PullError('Compressed response refused')
        length = response.getheader('Content-Length')
        if length is not None and (not length.isascii() or not length.isdecimal() or int(length) > max_bytes):
            raise PullError('Response length refused')
        body = response.read(max_bytes + 1)
        if not body or len(body) > max_bytes or (length is not None and int(length) != len(body)):
            raise PullError('Response size mismatch')
        return body
    except Exception:
        raise PullError('Government data request failed') from None
    finally:
        if conn is not None:
            conn.close()
