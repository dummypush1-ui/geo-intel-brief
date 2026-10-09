"""Inactive HTTPS connector candidate. Never imported by the running app.
No auto-run on import. Resolve then connect pinned public address, actual peer
check and hostname-verified TLS. Hard whole-fetch process deadline is owned by
runner.py, not socket timeouts alone. Local unit tests use injected mocks only.
"""
import base64
import http.client
import json
import math
import socket
import ssl
import time
from collector113_prep.transport_policy import endpoint_plan, decode_response, TransportRefused

UA = 'Mozilla/5.0 (compatible; GeoIntelMonitor/2.0; +https://render.com)'
class ConnectorRefused(ValueError):
    pass

def fetch_one(feeds, url, *, timeout=20, account):
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30:
        raise ConnectorRefused('Timeout shape')
    # Validate URL before a DNS call; public literal is supplied solely to check
    # installed URL policy and is not used as the real destination.
    checked = endpoint_plan(feeds, url, ('8.8.8.8',), '8.8.8.8')
    deadline = time.monotonic() + timeout
    def remaining():
        n = deadline - time.monotonic()
        if n <= 0: raise ConnectorRefused('Fetch wall budget')
        return n
    answers = socket.getaddrinfo(checked['hostname'], 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    remaining()
    if not 1 <= len(answers) <= 16: raise ConnectorRefused('DNS set budget')
    addresses = tuple(row[4][0] for row in answers)
    # Check ALL answers before opening any connection, rejecting mixed sets.
    endpoint_plan(feeds, url, addresses, addresses[0])
    family, kind, proto, _, target = answers[0]
    if family not in (socket.AF_INET, socket.AF_INET6) or kind != socket.SOCK_STREAM or proto != socket.IPPROTO_TCP or target[1] != 443:
        raise ConnectorRefused('DNS endpoint shape')
    if family == socket.AF_INET6 and (len(target) != 4 or target[2] != 0 or target[3] != 0):
        raise ConnectorRefused('IPv6 scope/flow refused')
    raw = None; tls = None; response = None
    try:
        raw = socket.socket(family, kind, proto)
        raw.settimeout(remaining())
        raw.connect(target)
        peer = raw.getpeername()[0]
        if peer != addresses[0]: raise ConnectorRefused('Pinned peer changed')
        plan = endpoint_plan(feeds, url, addresses, peer)
        context = ssl.create_default_context()
        if context.check_hostname is not True or context.verify_mode != ssl.CERT_REQUIRED:
            raise ConnectorRefused('Verified TLS required')
        raw.settimeout(remaining())
        tls = context.wrap_socket(raw, server_hostname=plan['tls_server_name'])
        tls.settimeout(remaining())
        if tls.getpeername()[0] != peer: raise ConnectorRefused('TLS peer changed')
        request = ('GET ' + plan['request_target'] + ' HTTP/1.1\r\nHost: ' + plan['hostname'] +
                   '\r\nUser-Agent: ' + UA + '\r\nAccept-Encoding: gzip, deflate\r\nConnection: close\r\n\r\n').encode('ascii')
        tls.sendall(request)
        response = http.client.HTTPResponse(tls)
        tls.settimeout(remaining()); response.begin()
        if response.headers.defects:
            raise ConnectorRefused('Malformed HTTP header parse')
        pairs = response.getheaders()
        if len(pairs) > 32: raise ConnectorRefused('Response header budget')
        headers = {}
        for k, v in pairs:
            key = k.lower()
            if key in headers: raise ConnectorRefused('Duplicate HTTP header')
            headers[key] = v
        # HTTPResponse may parse TE liberally. Accept only exact chunked without
        # CL. Raw compression body bytes are returned by HTTPResponse.read.
        transfer = headers.pop('transfer-encoding', None)
        if transfer is not None and (transfer.strip().lower() != 'chunked' or 'content-length' in headers or not response.chunked):
            raise ConnectorRefused('Ambiguous HTTP framing')
        # Validate metadata before any body read. No exception-string routing.
        if type(response.status) is not int or response.status != 200:
            raise ConnectorRefused('HTTP status or redirect refused')
        import re
        for key, value in headers.items():
            if (type(key) is not str or type(value) is not str or
                    not 1 <= len(key) <= 100 or len(value) > 2000 or
                    not re.fullmatch(r'[A-Za-z0-9-]+', key) or
                    '\r' in value or '\n' in value):
                raise ConnectorRefused('HTTP header shape')
        if headers.get('content-encoding', 'identity').strip().lower() not in ('identity','gzip','deflate'):
            raise ConnectorRefused('Content encoding')
        length = headers.get('content-length')
        if length is not None and (not re.fullmatch(r'[0-9]{1,8}',length.strip()) or int(length)>1048576):
            raise ConnectorRefused('Declared wire budget')
        # Close-delimited identity cannot distinguish clean EOF from truncated data.
        # Refuse even valid-looking content rather than silently accept truncation.
        encoding=headers.get('content-encoding','identity').strip().lower()
        if transfer is None and length is None and encoding=='identity':
            raise ConnectorRefused('Unverifiable close-delimited identity')
        chunks=[]; wire=0
        while True:
            tls.settimeout(remaining())
            # Never read beyond the body cap, even on a refused source.
            if wire==1048576:
                if length is not None and int(length)==wire:break
                raise ConnectorRefused('Body cap without complete framing')
            chunk = response.read(min(65536,1048576-wire))
            remaining()
            if not chunk: break
            wire += len(chunk)
            account(len(chunk))
            if wire > 1048576 or len(chunks) >= 4096: raise ConnectorRefused('Wire budget')
            chunks.append(chunk)
        if length is not None and wire!=int(length):
            raise ConnectorRefused('Truncated Content-Length body')
        result = decode_response(response.status, headers, chunks, deadline=deadline)
        return {'scope':'inactive_https_connector_candidate','url':url,
                'body_b64':base64.b64encode(result['bytes']).decode('ascii'),
                'wire_bytes':result['wire_bytes'],'decoded_bytes':result['decoded_bytes'],
                'hostname':plan['hostname'],'peer':peer,'tls_hostname_verified':True,
                'redirects':False,'delivery':False}
    finally:
        if response is not None: response.close()
        if tls is not None: tls.close()
        if raw is not None: raw.close()
